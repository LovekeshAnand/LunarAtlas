"""
API Key management endpoints.
Authenticated users can generate, list, and revoke API keys.
Keys follow the format: la_<32-hex-chars>
Only the SHA-256 hash is stored; the plaintext key is shown exactly once upon creation.
"""

import hashlib
import secrets
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Optional
from pydantic import BaseModel, Field
import logging

from app.api.v1.auth import get_current_user
from app.database.connection import db

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    label: str = Field("Default", max_length=100, description="Friendly label for the key")

class ApiKeyResponse(BaseModel):
    id: int
    key_prefix: str
    label: str
    is_active: bool
    created_at: str
    last_used: Optional[str] = None
    expires_at: Optional[str] = None

class ApiKeyCreated(BaseModel):
    """Returned exactly once when a new key is generated."""
    id: int
    key: str = Field(..., description="Full API key (shown only once)")
    key_prefix: str
    label: str
    message: str = "Store this key securely. It will not be shown again."


# ── Helpers ──────────────────────────────────────────────────────────────────

def _generate_api_key() -> str:
    """Generate a cryptographically secure API key with the la_ prefix."""
    return f"la_{secrets.token_hex(16)}"

def _hash_key(key: str) -> str:
    """SHA-256 hash of the raw API key for storage."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/api-keys", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    body: ApiKeyCreate = ApiKeyCreate(),
    current_user: Any = Depends(get_current_user),
):
    """Generate a new API key for the authenticated user."""
    user_id = current_user["id"]

    # Enforce a maximum of 5 active keys per user
    count_row = await db.fetch_one(
        "SELECT COUNT(*) AS cnt FROM api_keys WHERE user_id = $1 AND is_active = TRUE",
        user_id,
    )
    if count_row and count_row["cnt"] >= 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum of 5 active API keys reached. Revoke an existing key first.",
        )

    raw_key = _generate_api_key()
    key_hash = _hash_key(raw_key)
    key_prefix = raw_key[:12]  # "la_" + first 9 hex chars

    row = await db.fetch_one(
        """
        INSERT INTO api_keys (user_id, key_hash, key_prefix, label)
        VALUES ($1, $2, $3, $4)
        RETURNING id, key_prefix, label
        """,
        user_id,
        key_hash,
        key_prefix,
        body.label,
    )
    return ApiKeyCreated(
        id=row["id"],
        key=raw_key,
        key_prefix=row["key_prefix"],
        label=row["label"],
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(current_user: Any = Depends(get_current_user)):
    """List all API keys for the authenticated user."""
    rows = await db.fetch_all(
        """
        SELECT id, key_prefix, label, is_active,
               created_at::text, last_used::text, expires_at::text
        FROM api_keys
        WHERE user_id = $1
        ORDER BY created_at DESC
        """,
        current_user["id"],
    )
    return [dict(r) for r in rows]


@router.delete("/api-keys/{key_id}", status_code=200)
async def revoke_api_key(
    key_id: int,
    current_user: Any = Depends(get_current_user),
):
    """Revoke (deactivate) an API key."""
    result = await db.fetch_one(
        """
        UPDATE api_keys SET is_active = FALSE
        WHERE id = $1 AND user_id = $2
        RETURNING id
        """,
        key_id,
        current_user["id"],
    )
    if not result:
        raise HTTPException(status_code=404, detail="API key not found or already revoked")
    return {"detail": "API key revoked successfully", "id": key_id}
