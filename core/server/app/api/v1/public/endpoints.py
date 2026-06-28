from fastapi import APIRouter, HTTPException, Query, Header, Depends, Request
from typing import List, Optional, Dict, Tuple
import numpy as np
import hashlib
import time
import logging
from datetime import datetime

from app.schemas.public import (
    PublicResponseEnvelope,
    PublicMeta,
    PublicMission,
    PublicInstrument,
    PublicObservation,
    PublicMeasurement,
    PublicSpectrumPoint,
    PublicSpectrumDetail
)
from app.core.downsampling import lttb_downsample
from app.database.connection import db
from app.cache.redis_cache import cache, cached

from app.config import settings
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(RateLimiter(settings.RATE_LIMIT_REQUESTS_PER_MINUTE))])


def _hash_key(key: str) -> str:
    """SHA-256 hash of the raw API key for lookup."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Query(None, description="API Key (DEMO_KEY or la_xxx generated key)"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key", description="API Key header")
) -> Dict:
    """
    Validates API key passed via query parameter or request header.
    Returns a dict with user_id and api_key_id for usage logging.
    Supports:
      - 'DEMO_KEY' for sandbox access (no user association).
      - 'la_*' keys: looked up via SHA-256 hash in the api_keys table.
    """
    key = api_key or x_api_key
    if not key:
        raise HTTPException(
            status_code=401,
            detail="API Key is missing. Pass '?api_key=DEMO_KEY' or 'X-API-Key' header. "
                   "Generate a key from your Dashboard, or use 'DEMO_KEY' for testing."
        )

    if key == "DEMO_KEY":
        auth_info = {"user_id": None, "api_key_id": None, "key_label": "DEMO_KEY"}
        request.state.api_key_info = auth_info
        return auth_info

    if key.startswith("la_"):
        key_hash = _hash_key(key)
        try:
            row = await db.fetch_one(
                """
                SELECT k.id AS key_id, k.user_id, k.is_active, k.expires_at
                FROM api_keys k
                WHERE k.key_hash = $1
                """,
                key_hash,
            )
            if not row:
                raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key.")
            if not row["is_active"]:
                raise HTTPException(status_code=401, detail="Unauthorized: This API key has been revoked.")
            if row["expires_at"] and row["expires_at"] < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Unauthorized: This API key has expired.")

            # Update last_used timestamp (fire-and-forget)
            try:
                await db.execute(
                    "UPDATE api_keys SET last_used = NOW() WHERE id = $1", row["key_id"]
                )
            except Exception:
                pass

            auth_info = {"user_id": row["user_id"], "api_key_id": row["key_id"], "key_label": key[:12]}
            request.state.api_key_info = auth_info
            return auth_info
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            raise HTTPException(status_code=500, detail="Authentication system failure")

    raise HTTPException(
        status_code=401,
        detail="Unauthorized: Invalid API key format. Use a 'la_' prefixed key or 'DEMO_KEY'."
    )


async def log_api_usage(
    request: Request,
    auth: Dict,
    status_code: int,
    response_bytes: int,
    response_time_ms: float,
):
    """Record a public API call in the api_usage_log table."""
    try:
        await db.execute(
            """
            INSERT INTO api_usage_log
                (api_key_id, user_id, endpoint, method, status_code,
                 response_time_ms, response_bytes, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            auth.get("api_key_id"),
            auth.get("user_id"),
            request.url.path,
            request.method,
            status_code,
            response_time_ms,
            response_bytes,
            request.client.host if request.client else None,
            request.headers.get("user-agent", "")[:512],
        )
    except Exception as e:
        logger.warning(f"Failed to log API usage: {e}")


@router.get("/missions", response_model=PublicResponseEnvelope)
@cached(ttl=3600)
async def list_missions(
    limit: int = Query(10, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve planetary science missions list.
    """
    query = """
        SELECT mission_id, mission_code, mission_name, organization, launch_date, target_body, description
        FROM mission
        ORDER BY mission_id
        LIMIT $1 OFFSET $2
    """
    try:
        rows = await db.fetch_all(query, limit, offset)
        results = [PublicMission(**dict(row)) for row in rows]
        
        links = {
            "self": f"/api/v1/public/missions?limit={limit}&offset={offset}",
            "next": f"/api/v1/public/missions?limit={limit}&offset={offset + limit}" if len(rows) == limit else None,
            "prev": f"/api/v1/public/missions?limit={limit}&offset={max(0, offset - limit)}" if offset > 0 else None
        }
        return PublicResponseEnvelope(
            meta=PublicMeta(rate_limit_remaining=999),
            results=results,
            links=links
        )
    except Exception as e:
        logger.error(f"Error querying missions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch missions database catalog")


@router.get("/missions/{mission_code}", response_model=PublicResponseEnvelope)
@cached(ttl=3600)
async def get_mission_by_code(
    mission_code: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve metadata for a specific space mission by its code.
    """
    query = """
        SELECT mission_id, mission_code, mission_name, organization, launch_date, target_body, description
        FROM mission
        WHERE UPPER(mission_code) = UPPER($1)
    """
    try:
        row = await db.fetch_one(query, mission_code)
        if not row:
            raise HTTPException(status_code=404, detail=f"Mission '{mission_code}' not found")
        
        results = PublicMission(**dict(row))
        links = {
            "self": f"/api/v1/public/missions/{mission_code}",
            "parent": "/api/v1/public/missions"
        }
        return PublicResponseEnvelope(
            meta=PublicMeta(rate_limit_remaining=998),
            results=results,
            links=links
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying mission detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to query mission detail")


@router.get("/instruments", response_model=PublicResponseEnvelope)
@cached(ttl=3600)
async def list_instruments(
    mission_code: Optional[str] = Query(None, description="Filter instruments by mission code, e.g. CH3"),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve list of scientific instruments.
    """
    if mission_code:
        query = """
            SELECT i.instrument_id, i.mission_id, i.instrument_code, i.instrument_name, i.instrument_type, i.description
            FROM instrument i
            JOIN mission m ON i.mission_id = m.mission_id
            WHERE UPPER(m.mission_code) = UPPER($1)
            ORDER BY i.instrument_id
        """
        params = [mission_code]
    else:
        query = """
            SELECT instrument_id, mission_id, instrument_code, instrument_name, instrument_type, description
            FROM instrument
            ORDER BY instrument_id
        """
        params = []
        
    try:
        rows = await db.fetch_all(query, *params)
        results = [PublicInstrument(**dict(row)) for row in rows]
        links = {
            "self": f"/api/v1/public/instruments" + (f"?mission_code={mission_code}" if mission_code else "")
        }
        return PublicResponseEnvelope(
            meta=PublicMeta(rate_limit_remaining=997),
            results=results,
            links=links
        )
    except Exception as e:
        logger.error(f"Error querying instruments: {e}")
        raise HTTPException(status_code=500, detail="Failed to query instruments catalog")


@router.get("/observations", response_model=PublicResponseEnvelope)
@cached(ttl=3600)
async def list_observations(
    mission: Optional[str] = Query(None, description="Mission code filter, e.g. CH3"),
    instrument: Optional[str] = Query(None, description="Instrument code filter, e.g. LIBS"),
    target_name: Optional[str] = Query(None, description="Target body filter, e.g. Moon"),
    date: Optional[str] = Query(None, description="Filter observations by date in YYYY-MM-DD format"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    api_key: str = Depends(verify_api_key)
):
    """
    Query observation sessions conforming to PDS standards.
    """
    query = """
        SELECT DISTINCT
            o.observation_id, 
            o.session_id, 
            o.logical_identifier, 
            o.observation_code, 
            o.observation_number, 
            o.sub_index, 
            o.start_time, 
            o.stop_time, 
            o.pds_version_id, 
            o.information_model_version, 
            o.processing_level, 
            o.purpose,
            os.observation_date,
            os.target_description,
            fi.record_count
        FROM observation o
        JOIN observation_session os ON o.session_id = os.session_id
        JOIN dataset_version dv ON os.dataset_version_id = dv.dataset_version_id
        JOIN instrument_spec_libs isl ON dv.spec_id = isl.spec_id
        JOIN instrument i ON isl.instrument_id = i.instrument_id
        JOIN mission m ON i.mission_id = m.mission_id
        LEFT JOIN observation_file_info fi ON o.observation_id = fi.observation_id
        WHERE 1=1
    """
    params = []
    param_idx = 1
    
    if mission:
        query += f" AND UPPER(m.mission_code) = UPPER(${param_idx})"
        params.append(mission)
        param_idx += 1
        
    if instrument:
        query += f" AND UPPER(i.instrument_code) = UPPER(${param_idx})"
        params.append(instrument)
        param_idx += 1
        
    if target_name:
        query += f" AND (UPPER(os.target_description) LIKE UPPER('%' || ${param_idx} || '%') OR UPPER(o.logical_identifier) LIKE UPPER('%' || ${param_idx} || '%'))"
        params.append(target_name)
        param_idx += 1

    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
            query += f" AND os.observation_date = ${param_idx}"
            params.append(datetime.strptime(date, "%Y-%m-%d").date())
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
    query += f" ORDER BY os.observation_date DESC, o.start_time DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    params.extend([limit, offset])
    
    try:
        rows = await db.fetch_all(query, *params)
        results = [PublicObservation(**dict(row)) for row in rows]
        
        links = {
            "self": f"/api/v1/public/observations?limit={limit}&offset={offset}" + (f"&date={date}" if date else ""),
            "next": f"/api/v1/public/observations?limit={limit}&offset={offset + limit}" + (f"&date={date}" if date else "") if len(rows) == limit else None,
            "prev": f"/api/v1/public/observations?limit={limit}&offset={max(0, offset - limit)}" + (f"&date={date}" if date else "") if offset > 0 else None
        }
        return PublicResponseEnvelope(
            meta=PublicMeta(rate_limit_remaining=996),
            results=results,
            links=links
        )
    except Exception as e:
        logger.error(f"Error querying public observations: {e}")
        raise HTTPException(status_code=500, detail="Failed to query observations catalog")


@router.get("/measurements", response_model=PublicResponseEnvelope)
@cached(ttl=3600)
async def list_measurements(
    observation_id: Optional[str] = Query(None, description="Observation / file_info ID filter"),
    mission: Optional[str] = Query(None, description="Filter by mission code, e.g. CH3"),
    instrument: Optional[str] = Query(None, description="Filter by instrument code, e.g. LIBS"),
    date: Optional[str] = Query(None, description="Filter by observation date in YYYY-MM-DD format"),
    is_background: Optional[bool] = Query(None, description="Filter background zaps"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve public measurements list with operational telemetry.
    Supports filtering by observation_id, mission code, instrument code, and date.
    """
    query = """
        SELECT 
            m.measurement_id, 
            m.file_info_id as observation_id,
            m.measurement_index,
            m.time_utc, 
            m.measurement_count,
            m.operation_mode,
            m.measurement_type,
            m.is_background,
            m.integration_time_us, 
            m.number_of_pulses, 
            m.laser_energy_v
        FROM measurement_clean m
        LEFT JOIN observation_file_info ofi ON m.file_info_id = ofi.file_info_id
        LEFT JOIN observation o ON ofi.observation_id = o.observation_id
        LEFT JOIN observation_session os ON o.session_id = os.session_id
        LEFT JOIN dataset_version dv ON os.dataset_version_id = dv.dataset_version_id
        LEFT JOIN instrument_spec_libs isl ON dv.spec_id = isl.spec_id
        LEFT JOIN instrument i ON isl.instrument_id = i.instrument_id
        LEFT JOIN mission ms ON i.mission_id = ms.mission_id
        WHERE 1=1
    """
    params = []
    param_idx = 1
    
    if observation_id:
        query += f" AND (m.file_info_id = ${param_idx} OR ofi.observation_id = ${param_idx})"
        params.append(observation_id)
        param_idx += 1

    if mission:
        query += f" AND UPPER(ms.mission_code) = UPPER(${param_idx})"
        params.append(mission)
        param_idx += 1

    if instrument:
        query += f" AND UPPER(i.instrument_code) = UPPER(${param_idx})"
        params.append(instrument)
        param_idx += 1

    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
            query += f" AND os.observation_date = ${param_idx}"
            params.append(datetime.strptime(date, "%Y-%m-%d").date())
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if is_background is not None:
        query += f" AND m.is_background = ${param_idx}"
        params.append(is_background)
        param_idx += 1
        
    query += f" ORDER BY m.time_utc DESC, m.measurement_index ASC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    params.extend([limit, offset])
    
    try:
        rows = await db.fetch_all(query, *params)
        results = [PublicMeasurement(**dict(row)) for row in rows]
        
        link_params = f"limit={limit}&offset={offset}"
        if observation_id: link_params += f"&observation_id={observation_id}"
        if mission: link_params += f"&mission={mission}"
        if instrument: link_params += f"&instrument={instrument}"
        if date: link_params += f"&date={date}"
        
        links = {
            "self": f"/api/v1/public/measurements?{link_params}",
            "next": f"/api/v1/public/measurements?limit={limit}&offset={offset + limit}" + (f"&mission={mission}" if mission else "") + (f"&date={date}" if date else "") + (f"&observation_id={observation_id}" if observation_id else "") if len(rows) == limit else None,
            "prev": f"/api/v1/public/measurements?limit={limit}&offset={max(0, offset - limit)}" + (f"&mission={mission}" if mission else "") + (f"&date={date}" if date else "") + (f"&observation_id={observation_id}" if observation_id else "") if offset > 0 else None
        }
        return PublicResponseEnvelope(
            meta=PublicMeta(rate_limit_remaining=995),
            results=results,
            links=links
        )
    except Exception as e:
        logger.error(f"Error querying public measurements: {e}")
        raise HTTPException(status_code=500, detail="Failed to query measurements catalog")


@router.get("/spectra", response_model=PublicResponseEnvelope)
async def list_spectra(
    observation_id: Optional[str] = Query(None, description="Retrieve all spectra belonging to this observation ID"),
    date: Optional[str] = Query(None, description="Retrieve all spectra recorded on this date (YYYY-MM-DD)"),
    mission: Optional[str] = Query(None, description="Filter by mission code, e.g. CH3"),
    measurement_ids: Optional[str] = Query(None, description="Comma-separated list of specific measurement IDs to retrieve"),
    lambda_min: float = Query(164.35, description="Lower wavelength boundary in nm"),
    lambda_max: float = Query(878.26, description="Upper wavelength boundary in nm"),
    downsample: bool = Query(False, description="Apply scientific downsampling to reduce payload density"),
    zoom_level: int = Query(0, ge=0, le=5, description="Downsample density level (0-5)"),
    target_wavelengths: Optional[str] = Query(None, description="NIST wavelength peaks to preserve (comma-separated, e.g. 393.37,396.15)"),
    limit: int = Query(10, ge=1, le=50, description="Limit the number of measurements returned in bulk query"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve scientific spectrum lines for multiple measurements.
    Allows bulk fetching by observation ID, date, mission, or explicit list of measurement IDs.
    """
    # Parse target wavelengths
    parsed_targets: List[float] = []
    if target_wavelengths:
        try:
            parsed_targets = [float(w.strip()) for w in target_wavelengths.split(",") if w.strip()]
        except ValueError:
            logger.warning(f"Invalid target wavelengths format: {target_wavelengths}")

    # Build query for measurement IDs
    m_query = """
        SELECT m.measurement_id, o.processing_level
        FROM measurement_clean m
        JOIN observation_file_info ofi ON m.file_info_id = ofi.file_info_id
        JOIN observation o ON ofi.observation_id = o.observation_id
        JOIN observation_session os ON o.session_id = os.session_id
        JOIN dataset_version dv ON os.dataset_version_id = dv.dataset_version_id
        JOIN instrument_spec_libs isl ON dv.spec_id = isl.spec_id
        JOIN instrument i ON isl.instrument_id = i.instrument_id
        JOIN mission ms ON i.mission_id = ms.mission_id
        WHERE 1=1
    """
    m_params = []
    param_idx = 1
    
    if measurement_ids:
        ids_list = [i.strip() for i in measurement_ids.split(",") if i.strip()]
        m_query += f" AND m.measurement_id = ANY(${param_idx})"
        m_params.append(ids_list)
        param_idx += 1
    
    if observation_id:
        m_query += f" AND (m.file_info_id = ${param_idx} OR ofi.observation_id = ${param_idx})"
        m_params.append(observation_id)
        param_idx += 1

    if mission:
        m_query += f" AND UPPER(ms.mission_code) = UPPER(${param_idx})"
        m_params.append(mission)
        param_idx += 1

    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
            m_query += f" AND os.observation_date = ${param_idx}"
            m_params.append(datetime.strptime(date, "%Y-%m-%d").date())
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
            
    m_query += f" ORDER BY m.time_utc DESC, m.measurement_index ASC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    m_params.extend([limit, offset])
    
    try:
        rows = await db.fetch_all(m_query, *m_params)
        if not rows:
            return PublicResponseEnvelope(
                meta=PublicMeta(rate_limit_remaining=994),
                results=[],
                links={"self": f"/api/v1/public/spectra?limit={limit}&offset={offset}"}
            )
            
        m_ids = [row["measurement_id"] for row in rows]
        proc_levels = {row["measurement_id"]: row["processing_level"] for row in rows}
        
        # Query all spectral points for these measurements
        points_query = """
            SELECT 
                c.measurement_id,
                c.wavelength_nm, 
                c.intensity,
                cal.response_count AS raw_intensity
            FROM spectral_data_clean c
            LEFT JOIN spectral_data_raw cal 
              ON c.measurement_id = cal.measurement_id 
              AND c.wavelength_nm = cal.wavelength_nm
            WHERE 
                c.measurement_id = ANY($1)
                AND c.wavelength_nm BETWEEN $2 AND $3
            ORDER BY c.measurement_id, c.wavelength_nm
        """
        points_rows = await db.fetch_all(points_query, m_ids, lambda_min, lambda_max)
        
        from collections import defaultdict
        grouped_points = defaultdict(list)
        for row in points_rows:
            grouped_points[row["measurement_id"]].append(row)
            
        results = []
        for m_id in m_ids:
            m_points = grouped_points[m_id]
            if not m_points:
                continue
                
            data_points = []
            if downsample:
                # Prepare for downsampling
                data_arr = np.array([
                    [float(row['wavelength_nm']), float(row['intensity']), float(row['raw_intensity'] or row['intensity'])]
                    for row in m_points
                ])
                
                ds_result = lttb_downsample(
                    data=data_arr,
                    zoom_level=zoom_level,
                    lambda_min=lambda_min,
                    lambda_max=lambda_max,
                    target_wavelengths=parsed_targets if parsed_targets else None
                )
                
                for pt in ds_result['data']:
                    data_points.append(
                        PublicSpectrumPoint(
                            wavelength_nm=pt['wavelength_nm'],
                            intensity=pt['intensity'],
                            raw_intensity=pt.get('raw_plasma')
                        )
                    )
            else:
                for row in m_points:
                    data_points.append(
                        PublicSpectrumPoint(
                            wavelength_nm=float(row['wavelength_nm']),
                            intensity=float(row['intensity']),
                            raw_intensity=float(row['raw_intensity']) if row['raw_intensity'] is not None else None
                        )
                    )
                    
            wavelength_min = float(m_points[0]['wavelength_nm'])
            wavelength_max = float(m_points[-1]['wavelength_nm'])
            
            results.append(
                PublicSpectrumDetail(
                    measurement_id=m_id,
                    processing_level=proc_levels.get(m_id, "Cleaned (L2)"),
                    points_count=len(data_points),
                    wavelength_range={"min": wavelength_min, "max": wavelength_max},
                    data=data_points
                )
            )
            
        links = {
            "self": f"/api/v1/public/spectra?limit={limit}&offset={offset}" +
                    (f"&observation_id={observation_id}" if observation_id else "") +
                    (f"&date={date}" if date else "") +
                    (f"&measurement_ids={measurement_ids}" if measurement_ids else ""),
            "next": f"/api/v1/public/spectra?limit={limit}&offset={offset + limit}" +
                    (f"&observation_id={observation_id}" if observation_id else "") +
                    (f"&date={date}" if date else "") +
                    (f"&measurement_ids={measurement_ids}" if measurement_ids else "") if len(rows) == limit else None,
            "prev": f"/api/v1/public/spectra?limit={limit}&offset={max(0, offset - limit)}" +
                    (f"&observation_id={observation_id}" if observation_id else "") +
                    (f"&date={date}" if date else "") +
                    (f"&measurement_ids={measurement_ids}" if measurement_ids else "") if offset > 0 else None
        }
        
        return PublicResponseEnvelope(
            meta=PublicMeta(rate_limit_remaining=994),
            results=results,
            links=links
        )
    except Exception as e:
        logger.error(f"Error querying bulk spectra: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve bulk spectral data")


@router.get("/spectra/{measurement_id}", response_model=PublicResponseEnvelope)
async def get_spectrum_detail(
    measurement_id: str,
    lambda_min: float = Query(164.35, description="Lower wavelength boundary in nm"),
    lambda_max: float = Query(878.26, description="Upper wavelength boundary in nm"),
    downsample: bool = Query(False, description="Apply scientific downsampling to reduce payload density"),
    zoom_level: int = Query(0, ge=0, le=5, description="Downsample density level (0-5)"),
    target_wavelengths: Optional[str] = Query(None, description="NIST wavelength peaks to preserve (comma-separated, e.g. 393.37,396.15)"),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve scientific spectrum lines for a single measurement.
    Conforms to ISRO PDS4 catalog response structures.
    """
    # Parse target wavelengths
    parsed_targets: List[float] = []
    if target_wavelengths:
        try:
            parsed_targets = [float(w.strip()) for w in target_wavelengths.split(",") if w.strip()]
        except ValueError:
            logger.warning(f"Invalid target wavelengths format: {target_wavelengths}")
            
    # Try caching if standard parameters are used
    cache_key = cache.generate_key("public_spectrum", measurement_id, lambda_min, lambda_max, downsample, zoom_level, target_wavelengths or "")
    cached_val = await cache.get(cache_key)
    if cached_val:
        return PublicResponseEnvelope(**cached_val)
        
    # Query database
    query = """
        SELECT 
            c.wavelength_nm, 
            c.intensity,
            cal.response_count AS raw_intensity
        FROM spectral_data_clean c
        LEFT JOIN spectral_data_raw cal 
          ON c.measurement_id = cal.measurement_id 
          AND c.wavelength_nm = cal.wavelength_nm
        WHERE 
            c.measurement_id = $1
            AND c.wavelength_nm BETWEEN $2 AND $3
        ORDER BY c.wavelength_nm
    """
    
    try:
        rows = await db.fetch_all(query, measurement_id, lambda_min, lambda_max)
        if not rows:
            raise HTTPException(status_code=404, detail=f"Spectrum for measurement '{measurement_id}' not found")
            
        data_points = []
        if downsample:
            # Prepare for downsampling
            data_arr = np.array([
                [float(row['wavelength_nm']), float(row['intensity']), float(row['raw_intensity'] or row['intensity'])]
                for row in rows
            ])
            
            ds_result = lttb_downsample(
                data=data_arr,
                zoom_level=zoom_level,
                lambda_min=lambda_min,
                lambda_max=lambda_max,
                target_wavelengths=parsed_targets if parsed_targets else None
            )
            
            for pt in ds_result['data']:
                data_points.append(
                    PublicSpectrumPoint(
                        wavelength_nm=pt['wavelength_nm'],
                        intensity=pt['intensity'],
                        raw_intensity=pt.get('raw_plasma')
                    )
                )
        else:
            for row in rows:
                data_points.append(
                    PublicSpectrumPoint(
                        wavelength_nm=float(row['wavelength_nm']),
                        intensity=float(row['intensity']),
                        raw_intensity=float(row['raw_intensity']) if row['raw_intensity'] is not None else None
                    )
                )
                
        # Read observation session info for metadata
        session_query = """
            SELECT o.processing_level, o.logical_identifier
            FROM observation o
            JOIN measurement_clean m ON o.observation_id = m.file_info_id
            WHERE m.measurement_id = $1
            LIMIT 1
        """
        session_row = await db.fetch_one(session_query, measurement_id)
        proc_level = session_row['processing_level'] if session_row else "Cleaned (L2)"
        
        wavelength_min = float(rows[0]['wavelength_nm'])
        wavelength_max = float(rows[-1]['wavelength_nm'])
        
        results = PublicSpectrumDetail(
            measurement_id=measurement_id,
            processing_level=proc_level,
            points_count=len(data_points),
            wavelength_range={"min": wavelength_min, "max": wavelength_max},
            data=data_points
        )
        
        envelope = PublicResponseEnvelope(
            meta=PublicMeta(rate_limit_remaining=994),
            results=results,
            links={"self": f"/api/v1/public/spectra/{measurement_id}"}
        )
        
        # Cache results for 1 hour
        await cache.set(cache_key, envelope.model_dump(), ttl=3600)
        return envelope
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building public spectrum detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to construct public spectrum data product")
