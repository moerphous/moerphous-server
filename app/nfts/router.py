"""The nfts router module"""

import base64
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
    Union,
)

from app.auth import (
    schemas as auth_schemas,
)
from app.config import (
    settings,
)
from app.nfts import (
    crud as nfts_crud,
    schemas as nfts_schemas,
)
from app.utils import (
    dependencies,
    jwt,
)
from app.wallets import (
    schemas as wallets_schemas,
)

router = APIRouter(prefix="/api/v1")
pinata = PinataPy(settings().PINATA_API_KEY, settings().PINATA_API_SECRET)


@router.post(
    "/nft/mint-offer",
    name="nft:mint-nft-with-offer",
    response_model=auth_schemas.ResponseSchema,
    responses={
        200: {
            "model": auth_schemas.ResponseSchema,
            "description": "A response object that indicates an nft"
            " has been minted successfully!",
        },
    },
)
async def mint_nft_token_with_offer(
    nft_info: nfts_schemas.NFTObjectSchema,
    current_wallet: Any = Depends(jwt.get_current_active_wallet),
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    mint an nft token and create a sell offer.
    """
    meta_data = f"{nft_info.picture},{nft_info.title},{nft_info.price}"
    await nfts_crud.mint_nft_token(
        current_wallet.classic_address, meta_data, session, True
    )
    return {"status_code": 200, "message": "NFT minted successfully!"}


@router.post(
    "/nft/upload-image",
    name="nft:upload-image",
    response_model=Union[
        auth_schemas.ResponseSchema, nfts_schemas.UploadImageResponseSchema
    ],
    responses={
        400: {
            "model": auth_schemas.ResponseSchema,
            "description": "A response object that indicates something went wrong!",
        },
        200: {
            "model": nfts_schemas.UploadImageResponseSchema,
            "description": "A response object that contains an ipfs url of the image.",
        },
    },
)
async def upload_nft_image(
    file: UploadFile = File(...),
    current_wallet: wallets_schemas.WalletObjectSchema = Depends(
        jwt.get_current_active_wallet
    ),
) -> Dict[str, Any]:
    """
    Upload nft image to ipfs.
    """
    try:
        file_bytes = file.file.read()
        temp = NamedTemporaryFile(delete=False)
        with temp as temp_file:
            temp_file.write(file_bytes)
        result = pinata.pin_file_to_ipfs(temp.name)
        image_url = (
            f"https://ipfs.io/ipfs/{result['IpfsHash']}/{temp.name.split('/')[-1]}"
        )
        return {"status_code": "200", "url": image_url}
    except Exception:
        return {"status_code": 400, "message": "Something went wrong!"}
    finally:
        os.remove(temp.name)


@router.post(
    "/nft/upload-mint-nft",
    name="nft:upload-mint-nft",
    response_model=auth_schemas.ResponseSchema,
    responses={
        200: {
            "model": auth_schemas.ResponseSchema,
            "description": "A response object that indicates an nft"
            " has been minted successfully!",
        },
    },
)
async def upload_nft_image_and_mint_nft(
    nft_info: nfts_schemas.NFTBase64ObjectSchema,
    current_wallet: Any = Depends(jwt.get_current_active_wallet),
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    Upload a base64 encoded image to ipfs and mint it
    """
    base64_bytes = nft_info.picture.encode("ascii")
    file_bytes = base64.b64decode(base64_bytes)
    temp = NamedTemporaryFile(delete=False)
    with temp as temp_file:
        temp_file.write(file_bytes)
    result = pinata.pin_file_to_ipfs(temp.name)
    image_url = f"https://ipfs.io/ipfs/{result['IpfsHash']}/{temp.name.split('/')[-1]}"
    meta_data = (
        f"{nft_info.author_avatar},{image_url},{nft_info.title},{nft_info.price}"
    )
    await nfts_crud.mint_nft_token(
        current_wallet.classic_address, meta_data, session, True
    )
    return {"status_code": 200, "message": "NFT minted successfully!"}


@router.get(
    "/nft/get-wallet-nfts",
    name="nft:get-wallet-nfts",
    response_model=nfts_schemas.ResponseSchema,
    responses={
        200: {
            "model": Any,
            "description": "A response object that contains info about"
            " a given wallet nfts.",
        },
    },
)
async def fetch_all_nfts(
    current_wallet: Any = Depends(jwt.get_current_active_wallet),
) -> Dict[str, Any]:
    """
    Fetch all nfts for the authenticated wallet.
    """
    results = await nfts_crud.get_all_nfts(current_wallet.classic_address)
    return results


@router.get(
    "/nft/get-all",
    name="nft:get-wallets-nfts",
    response_model=nfts_schemas.ResponseSchema,
    responses={
        200: {
            "model": nfts_schemas.ResponseSchema,
            "description": "A response object that contains info about"
            " a all nfts available on the marketplace.",
        },
    },
)
async def fetch_all_wallets_nfts(
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    Fetch all nfts for all registered wallets
    """
    results = await nfts_crud.get_all_wallets_nfts(session)
    return results
