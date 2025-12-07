from fastapi import APIRouter, UploadFile, File
from typing import List
from app.utils.upload import save_upload_file, save_multiple_files

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/single")
async def upload_single_image(file: UploadFile = File(...)):
    url = await save_upload_file(file)
    return {"url": url}

@router.post("/multiple")
async def upload_multiple_images(files: List[UploadFile] = File(...)):
    urls = await save_multiple_files(files)
    return {"urls": urls}
