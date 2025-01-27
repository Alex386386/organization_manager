from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings


def check_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Функция проверки корректности поступающего токена."""
    if credentials:
        token = credentials.credentials
        if token != settings.line_provider_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid!"
            )
        return token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не предоставлены учетные данные!",
        )
