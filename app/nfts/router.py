"""The nfts router module"""

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
    # response_model=Any,
    # responses={
    #     201: {
    #         "model": Any,
    #         "description": "A response object that contains info about"
    #         " a wallet.",
    #     },
    # },
)
async def mint_nft_token_with_offer(
    nft_info: nfts_schemas.NFTObjectSchema,
    current_wallet: Any = Depends(jwt.get_current_active_wallet),
    session: AIOSession = Depends(dependencies.get_db_transactional_session),
) -> Dict[str, Any]:
    """
    Generate a faucet wallet.
    """
    meta_data = f"{nft_info.picture},{nft_info.title},{nft_info.price}"
    results = await nfts_crud.mint_nft_token(
        current_wallet.classic_address, meta_data, session, True
    )
    return results


@router.post(
    "/nft/upload-image",
    name="nft:upload-image",
    # response_model=Any,
    # responses={
    #     201: {
    #         "model": Any,
    #         "description": "A response object that contains info about"
    #         " a wallet.",
    #     },
    # },
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
