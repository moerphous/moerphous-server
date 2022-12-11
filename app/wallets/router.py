"""The wallets router module"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)
from odmantic.session import (
    AIOSession,
)
import os
from pinatapy import (
    PinataPy,
)
from tempfile import (
    NamedTemporaryFile,
)
from typing import (
    Any,
    Dict,
)

from app.auth import (
    schemas as auth_schemas,
)
from app.config import (
    settings,
)
from app.utils import (
    dependencies,
    jwt,
)
from app.wallets import (
    crud as wallets_crud,
    schemas as wallets_schemas,
)

router = APIRouter(prefix="/api/v1")
pinata = PinataPy(settings().PINATA_API_KEY, settings().PINATA_API_SECRET)


@router.get(
    "/wallet",
    name="wallet:get-info",
)
async def get_wallet_info(
    current_wallet: Any = Depends(jwt.get_current_active_wallet),
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    Get wallet info given a token provided in a request header.
    """
    wallet = await wallets_crud.get_wallet_info(current_wallet.classic_address, session)
    return {
        "wallet": wallet,
        "status_code": 200,
        "message": "Welcome to Moerphous.",
    }


@router.post(
    "/wallet",
    name="wallet:create",
    response_model=wallets_schemas.WalletObjectSchema,
    responses={
        201: {
            "model": wallets_schemas.WalletObjectSchema,
            "description": "A response object that contains info about" " a wallet.",
        },
    },
)
async def create_faucet_wallet(
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    Generate a faucet wallet.
    """
    results = await wallets_crud.create_faucet_wallet(session)
    return results


@router.put(
    "/wallet/image",
    name="wallet:update-image",
    response_model=auth_schemas.ResponseSchema,
    responses={
        200: {
            "model": auth_schemas.ResponseSchema,
            "description": "A response object that contains info about" " a wallet.",
        },
    },
)
async def upload_author_image(
    file: UploadFile = File(...),
    current_wallet: Any = Depends(jwt.get_current_active_wallet),
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    Upload an image to IPFS.
    """
    try:
        file_bytes = file.file.read()
        temp = NamedTemporaryFile(delete=False)
        with temp as temp_file:
            temp_file.write(file_bytes)
        result = pinata.pin_file_to_ipfs(temp.name)
        image_url = (
            f"https://ipfs.io/ipfs/{result['IpfsHash']}/{temp.name.split('/')[-1]}.png"
        )
        await wallets_crud.update_wallet_image(
            image_url, current_wallet.classic_address, session
        )
        return {
            "status_code": 200,
            "message": "Profile picture has been uploaded successfully!",
        }

    except Exception as err:
        return {"status_code": 400, "message": str(err)}
    finally:
        os.remove(temp.name)


@router.put(
    "/wallet/info",
    name="wallet:update-wallet-info",
    response_model=auth_schemas.ResponseSchema,
    responses={
        200: {
            "model": auth_schemas.ResponseSchema,
            "description": "A response object that contains info about" " a wallet.",
        },
    },
)
async def update_wallet_info(
    wallet_info: wallets_schemas.WalletInfo,
    current_wallet: Any = Depends(jwt.get_current_active_wallet),
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    An endpoint for updating users personel info.
    """
    await wallets_crud.update_wallet_info(
        wallet_info, current_wallet.classic_address, session, pinata
    )
    return {
        "status_code": 200,
        "message": "Your wallet information has been updated successfully!",
    }
