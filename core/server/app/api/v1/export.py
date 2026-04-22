from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response, StreamingResponse
import orjson
import io
import csv

from app.api.v1.endpoints import get_spectrum

router = APIRouter()

@router.get("/json", response_class=Response)
async def export_spectrum_json(
    measurement_id: str = Query(..., description="Measurement ID"),
    lambda_min: float = Query(200.0, description="Minimum wavelength (nm)"),
    lambda_max: float = Query(800.0, description="Maximum wavelength (nm)"),
    zoom_level: int = Query(0, description="Discrete zoom level (0-5)"),
    force_raw: bool = Query(True, description="By default export raw data")
):
    """
    Export spectral data as JSON string for download.
    """
    try:
        response = await get_spectrum(
            measurement_id=measurement_id,
            lambda_min=lambda_min,
            lambda_max=lambda_max,
            zoom_level=zoom_level,
            use_cache=True,
            force_raw=force_raw
        )
        
        # In case the response is a dict directly or a Pydantic model
        if hasattr(response, "model_dump"):
            data_dump = response.model_dump()
        else:
            data_dump = response

        json_bytes = orjson.dumps(data_dump, option=orjson.OPT_INDENT_2)
        
        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="spectrum_{measurement_id}.json"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/csv")
async def export_spectrum_csv(
    measurement_id: str = Query(..., description="Measurement ID"),
    lambda_min: float = Query(200.0, description="Minimum wavelength (nm)"),
    lambda_max: float = Query(800.0, description="Maximum wavelength (nm)"),
    zoom_level: int = Query(0, description="Discrete zoom level (0-5)"),
    force_raw: bool = Query(True, description="By default export raw data")
):
    """
    Export spectral data as CSV file for download.
    """
    try:
        response = await get_spectrum(
            measurement_id=measurement_id,
            lambda_min=lambda_min,
            lambda_max=lambda_max,
            zoom_level=zoom_level,
            use_cache=True,
            force_raw=force_raw
        )
        
        if hasattr(response, "model_dump"):
            data_dump = response.model_dump()
        else:
            data_dump = response
            
        data_points = data_dump.get("data", [])
        
        def iter_csv():
            yield "wavelength_nm,intensity\n"
            for pt in data_points:
                # Based on downsampled or raw
                if "wavelength_nm" in pt:
                    yield f"{pt['wavelength_nm']},{pt['intensity']}\n"
                elif "lambda_center" in pt:
                    # In case of downsampled buckets
                    yield f"{pt['lambda_center']},{pt['intensity_max']}\n"
                    
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="spectrum_{measurement_id}.csv"'
            }
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
