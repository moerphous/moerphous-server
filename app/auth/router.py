"""Auth router module."""

from fastapi import (
    APIRouter,
    Depends,
)
from odmantic.session import (
    AIOSession,
)
from typing import (
    Any,
    Dict,
    Union,
)

from app.auth import (
    crud as auth_crud,
    schemas as auth_schemas,
)
from app.utils import (
    dependencies,
)

router = APIRouter(prefix="/api/v1")


@router.post(
    "/auth/login",
    response_model=Union[auth_schemas.WalletLoginSchema, auth_schemas.ResponseSchema],
    status_code=200,
    name="auth:login",
    responses={
        200: {
            "model": auth_schemas.WalletLoginSchema,
            "description": "A response object contains an access token for a wallet"
            " e.g. Token value: {access_token: 'abcdefg12345token', token_type: 'Bearer'}",
        },
        401: {
            "model": auth_schemas.ResponseSchema,
            "description": "A response object indicates that invalid wallet address"
            " were provided!",
        },
        404: {
            "model": auth_schemas.ResponseSchema,
            "description": "A response object indicates that a wallet"
            " was not found!",
        },
    },
)
async def login(
    wallet: auth_schemas.TokenData,
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    Authenticate a wallet.
    """
    result = await auth_crud.wallet_login(wallet.classic_address, session)
    return result
