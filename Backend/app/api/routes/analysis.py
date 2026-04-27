from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.analysis import ProjectAnalysisResponse
from app.services.analysis.service import analyze_zip_project


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/upload", response_model=ProjectAnalysisResponse)
async def upload_project(file: UploadFile = File(...)) -> ProjectAnalysisResponse:
    filename = file.filename or "project.zip"
    try:
        content = await file.read()
        return analyze_zip_project(filename, content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project analysis failed.",
        ) from exc
