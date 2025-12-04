import os
import uuid
from typing import List
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

# Diretório para salvar imagens
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Extensões permitidas
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Tamanho máximo: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_image(file: UploadFile) -> None:
    """Valida se o arquivo é uma imagem válida"""
    
    # Verifica extensão
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato não permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Verifica tipo MIME
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ser uma imagem"
        )

async def save_upload_file(file: UploadFile) -> str:
    """Salva o arquivo e retorna a URL"""
    
    validate_image(file)
    
    # Gera nome único
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Salva o arquivo
    contents = await file.read()
    
    # Verifica tamanho
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande. Máximo: 5MB"
        )
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Retorna URL relativa
    return f"/uploads/products/{unique_filename}"

async def save_multiple_files(files: List[UploadFile]) -> List[str]:
    """Salva múltiplos arquivos"""
    
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo de 5 imagens por produto"
        )
    
    urls = []
    for file in files:
        url = await save_upload_file(file)
        urls.append(url)
    
    return urls

def delete_file(file_url: str) -> None:
    """Delete um arquivo do servidor"""
    try:
        # Extrai o nome do arquivo da URL
        filename = Path(file_url).name
        file_path = UPLOAD_DIR / filename
        
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Erro ao deletar arquivo: {e}")