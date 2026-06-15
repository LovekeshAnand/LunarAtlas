"""
API Usage analytics endpoints.
Authenticated users can view their own usage statistics and raw logs.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Optional
from pydantic import BaseModel, Field
import logging

from app.api.v1.auth import get_current_user
from app.database.connection import db

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class UsageSummary(BaseModel):
    total_requests_30d: int = 0
    total_bytes_30d: int = 0
    active_keys: int = 0
    most_used_endpoint: Optional[str] = None
    daily_breakdown: list[dict] = Field(default_factory=list)
    endpoint_breakdown: list[dict] = Field(default_factory=list)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/usage/summary", response_model=UsageSummary)
async def get_usage_summary(current_user: Any = Depends(get_current_user)):
    """
    Aggregate usage statistics for the authenticated user over the last 30 days.
    Includes daily request counts, endpoint breakdowns, and total data transferred.
    """
    user_id = current_user["id"]

    # Total requests and bytes in last 30 days
    totals = await db.fetch_one(
        """
        SELECT
            COALESCE(COUNT(*), 0) AS total_requests,
            COALESCE(SUM(response_bytes), 0) AS total_bytes
        FROM api_usage_log
        WHERE user_id = $1
          AND created_at >= NOW() - INTERVAL '30 days'
        """,
        user_id,
    )

    # Active keys count
    keys_row = await db.fetch_one(
        "SELECT COUNT(*) AS cnt FROM api_keys WHERE user_id = $1 AND is_active = TRUE",
        user_id,
    )

    # Most used endpoint
    top_endpoint = await db.fetch_one(
        """
        SELECT endpoint, COUNT(*) AS cnt
        FROM api_usage_log
        WHERE user_id = $1
          AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY endpoint
        ORDER BY cnt DESC
        LIMIT 1
        """,
        user_id,
    )

    # Daily breakdown (last 30 days)
    daily_rows = await db.fetch_all(
        """
        SELECT
            DATE(created_at) AS day,
            COUNT(*) AS requests,
            COALESCE(SUM(response_bytes), 0) AS bytes
        FROM api_usage_log
        WHERE user_id = $1
          AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY day ASC
        """,
        user_id,
    )

    # Endpoint breakdown
    endpoint_rows = await db.fetch_all(
        """
        SELECT
            endpoint,
            COUNT(*) AS requests,
            ROUND(AVG(response_time_ms)::numeric, 1) AS avg_response_ms,
            COALESCE(SUM(response_bytes), 0) AS total_bytes
        FROM api_usage_log
        WHERE user_id = $1
          AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY endpoint
        ORDER BY requests DESC
        """,
        user_id,
    )

    return UsageSummary(
        total_requests_30d=totals["total_requests"] if totals else 0,
        total_bytes_30d=totals["total_bytes"] if totals else 0,
        active_keys=keys_row["cnt"] if keys_row else 0,
        most_used_endpoint=top_endpoint["endpoint"] if top_endpoint else None,
        daily_breakdown=[
            {"day": str(r["day"]), "requests": r["requests"], "bytes": r["bytes"]}
            for r in daily_rows
        ],
        endpoint_breakdown=[
            {
                "endpoint": r["endpoint"],
                "requests": r["requests"],
                "avg_response_ms": float(r["avg_response_ms"]) if r["avg_response_ms"] else 0,
                "total_bytes": r["total_bytes"],
            }
            for r in endpoint_rows
        ],
    )


@router.get("/usage/log")
async def get_usage_log(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: Any = Depends(get_current_user),
):
    """Paginated raw usage log entries for the authenticated user."""
    rows = await db.fetch_all(
        """
        SELECT
            l.id,
            l.endpoint,
            l.method,
            l.status_code,
            l.response_time_ms,
            l.response_bytes,
            l.ip_address,
            l.created_at::text,
            k.key_prefix
        FROM api_usage_log l
        LEFT JOIN api_keys k ON l.api_key_id = k.id
        WHERE l.user_id = $1
        ORDER BY l.created_at DESC
        LIMIT $2 OFFSET $3
        """,
        current_user["id"],
        limit,
        offset,
    )
    return [dict(r) for r in rows]
