"""The utils jwt module."""

from datetime import (
    datetime,
    timedelta,
)
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)
import jwt
from jwt import (
    PyJWTError,
)
from odmantic.session import (
    AIOSession,
)
from pydantic import (
    ValidationError,
)
from typing import (
    Any,
    Dict,
    Optional,
    Union,
)

from app.auth import (
    crud as auth_crud,
    schemas as auth_schemas,
)
from app.config import (
    settings,
)
from app.utils import (
    dependencies,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="JWT")

JWT_SECRET_KEY = settings().JWT_SECRET_KEY
JWT_ALGORITHM = "HS256"


def get_token_wallet(token: str = Depends(oauth2_scheme)) -> str:
    """
    Get a token value.
    Args:
        token (str): token to be verified
    Returns:
        str: a token
    """
    return token


async def create_access_token(
    *, data: Dict[str, Any], expires_delta: timedelta
) -> Dict[str, Any]:
    """
    Create a token.
    Args:
        data (dict): data to be encoded in the token
        expires_delta (datetime.timedelta): expires date, 1 hour
        if not provided
    Returns:
        dict: token dict
    """
    try:
        payload = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=15)
        payload.update({"exp": expire})
        encoded_jwt_token = jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )
        return {"access_token": encoded_jwt_token, "token_type": "bearer"}
    except Exception:
        return {"message": "An error has occurred while generating an access" " token!"}


async def get_current_wallet(
    token: str = Depends(oauth2_scheme),
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Optional[Dict[str, Any]]:
    """
    This function is used to get the current wallet.
    Args:
        token (str, optional): The token of the wallet. Defaults to None.
        session (odmantic.session.AIOSession): A MongoDB transactional session.
    Raises:
        credentials_exception: If the token is invalid.
        credentials_exception: If the token is expired.
        credentials_exception: If the token is not found.
    Returns:
        dict: The wallet object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized Wallet!",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        expires = payload.get("exp")
        classic_address = payload.get("sub")
        if not classic_address:
            raise credentials_exception
        token_data = auth_schemas.TokenData(classic_address=classic_address)
        wallet = await auth_crud.find_existed_wallet(
            token_data.classic_address, session
        )
        if not wallet:
            raise credentials_exception
        # check token expiration
        if expires is None:
            raise credentials_exception
        if datetime.utcnow() > datetime.utcfromtimestamp(expires):
            raise credentials_exception
        return wallet
    except (PyJWTError, ValidationError):
        raise credentials_exception


def get_current_active_wallet(
    current_wallet: Any = Depends(get_current_wallet),
) -> Union[Any, HTTPException]:
    """
    This function checks if a wallet is active or not.
    Args:
        current_wallet (WalletObjectSchema): The wallet object.
    Raises:
        HTTPException: If the token is invalid.
    Returns:
        dict: The current wallet object.
    """
    if current_wallet.wallet_status == 0:
        raise HTTPException(status_code=400, detail="Inactive Wallet!")
    return current_wallet
