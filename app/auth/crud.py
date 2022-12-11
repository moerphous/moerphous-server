"""Auth Crud module."""

from datetime import (
    timedelta,
)
from odmantic.session import (
    AIOSession,
)
from typing import (
    Any,
    Dict,
)

from app.auth import (
    schemas as auth_schemas,
)
from app.utils import (
    jwt,
)
from app.wallets import (
    models as wallets_models,
)


async def find_existed_wallet(
    classic_address: str, session: AIOSession
) -> wallets_models.Wallet:
    """
    A method to check if the wallet exists in the database.

    Args:
        classic_address (str) : A wallet classic address.
        session (odmantic.session.AIOSession) : Odmantic session object.

    Returns:
        wallets_models.Wallet: A wallet model object.
    """
    wallet = await session.find_one(
        wallets_models.Wallet, wallets_models.Wallet.classic_address == classic_address
    )
    return wallet


async def wallet_login(classic_address: str, session: AIOSession) -> Dict[str, Any]:
    """
    A method to fetch and return serialized token info upon logging in.

    Args:
        classic_address (str) : A wallet classic address.
        session (odmantic.session.AIOSession) : Odmantic session object.

    Returns:
        Dict[str, Any]: a dict object that contains info about a given wallet.
    """
    wallet_obj = await find_existed_wallet(classic_address, session)
    if not wallet_obj:
        return {"status_code": 404, "message": "Wallet not found!"}
    wallet = auth_schemas.TokenData(classic_address=wallet_obj.classic_address)
    if not wallet:
        return {"status_code": 401, "message": "Wallet not registered!"}

    access_token_expires = timedelta(days=15)
    access_token = await jwt.create_access_token(
        data={"sub": classic_address},
        expires_delta=access_token_expires,
    )
    return {"status_code": 200, "access_token": access_token["access_token"]}
