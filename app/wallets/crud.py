"""The wallets crud module"""

from datetime import (
    timedelta,
)
from odmantic.session import (
    AIOSession,
)
from pinatapy import (
    PinataPy,
)
import requests
from tempfile import (
    NamedTemporaryFile,
)
from typing import (
    Any,
    Dict,
    List,
)
from xrpl.asyncio.account import (
    get_account_info,
    get_balance,
)
from xrpl.asyncio.clients import (
    AsyncJsonRpcClient,
)
from xrpl.asyncio.wallet import (
    generate_faucet_wallet,
)
from xrpl.models.requests import (
    AccountNFTs,
)
from xrpl.utils import (
    drops_to_xrp,
    hex_to_str,
)

from app.config import (
    settings,
)
from app.nfts import (
    crud as nfts_crud,
)
from app.utils import (
    jwt,
)
from app.wallets import (
    models as wallets_models,
    schemas as wallets_schemas,
)


async def create_faucet_wallet(session: AIOSession) -> Dict[str, Any]:
    """
    A method to insert a wallet in the database given a classic_address
    generated from a faucet wallet.

    Args:
        session (odmantic.session.AIOSession) : odmantic session object.
    Returns:
        Dict[str, Any]: A dict that represents the response object.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    wallet = await generate_faucet_wallet(client, debug=True)
    access_token_expires = timedelta(days=30)
    access_token = await jwt.create_access_token(
        data={"sub": wallet.classic_address},
        expires_delta=access_token_expires,
    )
    wallet_instance = await session.find_one(
        wallets_models.Wallet,
        wallets_models.Wallet.classic_address == wallet.classic_address,
    )
    if not wallet_instance:
        # create a new wallet
        wallet_instance = wallets_models.Wallet(
            classic_address=wallet.classic_address, seed=wallet.seed
        )
        await session.save(wallet_instance)

    account_info = await get_account_info(wallet.classic_address, client, "validated")

    return {
        "token": access_token["access_token"],
        "account_info": account_info.result,
        "message": "A new wallet has been generated successfully!",
        "status_code": 201,
    }


async def get_wallet_info(classic_address: str, session: AIOSession) -> Dict[str, Any]:
    """
    A method to fetch wallet info.

    Args:
        classic_address (str) : A wallet classic address.
        session (odmantic.session.AIOSession) : odmantic session object.
    Returns:
        Dict[str, Any]: A dict that represents the account info object.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    wallet = await session.find_one(
        wallets_models.Wallet, wallets_models.Wallet.classic_address == classic_address
    )
    wallet = wallet.dict()
    wallet["id"] = str(wallet["id"])
    wallet.pop("seed")
    balance = await get_balance(classic_address, client)
    # fetch data from NFTokens
    response = await client.request(
        AccountNFTs(
            account=classic_address,
        )
    )
    account_nfts = response.result["account_nfts"]
    first_name, bio, profile_picture = [
        None,
    ] * 3
    for nft_token in account_nfts:
        meta_data_url = hex_to_str(nft_token["URI"])
        if "png" not in meta_data_url:
            meta_data = requests.get(url=meta_data_url, timeout=30).text
            meta_data_array = meta_data.split(",")
            if len(meta_data_array) == 2:
                first_name, bio = meta_data_array
        elif "png" in meta_data_url:
            profile_picture = meta_data_url[:-4]
    wallet.update(
        {
            "first_name": first_name,
            "bio": bio,
            "author_avatar": profile_picture,
            "balance": float(drops_to_xrp(str(balance))),
        }
    )
    return wallet


async def update_wallet_info(
    wallet_info: wallets_schemas.WalletInfo,
    classic_address: str,
    session: AIOSession,
    pinata: PinataPy,
) -> Dict[str, Any]:
    """
    A method to update a wallet first name and bio meta data.

    Args:
        wallet_info (wallets_schemas.WalletInfo) : wallet info schema.
        classic_address (str) : A wallet classic address.
        session (odmantic.session.AIOSession) : odmantic session object.
        pinata (pinatapy.PinataPy): A pinatapy object instance.

    Returns:
        Dict[str, Any]: A dict that represents the account info object.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    response = await client.request(
        AccountNFTs(
            account=classic_address,
        )
    )
    account_nfts = response.result["account_nfts"]
    for nft_token in account_nfts:
        meta_data_url = hex_to_str(nft_token["URI"])
        # burn it, then mint a new one.
        if "png" not in meta_data_url:
            meta_data = requests.get(url=meta_data_url, timeout=30).text
            meta_data_array = meta_data.split(",")
            if len(meta_data_array) == 2:
                await nfts_crud.burn_nft_token(
                    classic_address, nft_token["NFTokenID"], session
                )
                break
    # mint a new nft given the new first_name and bio
    temp1 = NamedTemporaryFile(delete=False)
    with temp1 as file:
        file.write(f"{wallet_info.first_name},{wallet_info.bio}".encode())
    result = pinata.pin_file_to_ipfs(temp1.name)
    meta_data_url = (
        f"https://ipfs.io/ipfs/{result['IpfsHash']}/{temp1.name.split('/')[-1]}"
    )
    return await nfts_crud.mint_nft_token(classic_address, meta_data_url, session)


async def update_wallet_image(
    image_url: str, classic_address: str, session: AIOSession
) -> Dict[str, Any]:
    """
    A method to update a wallet first name and bio meta data.

    Args:
        image_url (str) : Image URL to be minted.
        classic_address (str) : A wallet classic address.
        session (odmantic.session.AIOSession) : odmantic session object.

    Returns:
        Dict[str, Any]: A dict that represents the account info object.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    response = await client.request(
        AccountNFTs(
            account=classic_address,
        )
    )
    account_nfts = response.result["account_nfts"]
    for nft_token in account_nfts:
        meta_data_url = hex_to_str(nft_token["URI"])
        # burn it, then mint a new one.
        if "png" in meta_data_url:
            await nfts_crud.burn_nft_token(
                classic_address, nft_token["NFTokenID"], session
            )
            break
    # mint a new nft given the image url
    return await nfts_crud.mint_nft_token(classic_address, image_url, session)


async def get_all_wallet_info(session: AIOSession) -> List[Any]:
    """
    A method to fetch top 9 wallets info.

    Args:
        session (odmantic.session.AIOSession) : odmantic session object.
    Returns:
        Dict[str, Any]: A list of  dicts that contains all wallets info.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    all_registered_wallets = await session.find(wallets_models.Wallet)
    results = []
    for wallet in all_registered_wallets:
        wallet = wallet.dict()
        wallet["id"] = str(wallet["id"])
        wallet.pop("seed")
        response = await client.request(
            AccountNFTs(
                account=wallet["classic_address"],
            )
        )
        account_nfts = response.result["account_nfts"]
        first_name, bio, profile_picture = [
            None,
        ] * 3
        total_nfts = 0
        for nft_token in account_nfts:
            meta_data_url = hex_to_str(nft_token["URI"])
            if "png" not in meta_data_url:
                try:
                    meta_data = requests.get(url=meta_data_url, timeout=30).text
                    meta_data_array = meta_data.split(",")
                except Exception:
                    meta_data_array = meta_data.split(",")[1:4]
                    meta_data_array[2] = meta_data_array[2].split(":")[0]
                if len(meta_data_array) == 2:
                    first_name, bio = meta_data_array
                elif len(meta_data_array) in [3, 5]:
                    total_nfts += 1
            elif "png" in meta_data_url:
                profile_picture = meta_data_url[:-4]
        wallet.update(
            {
                "first_name": first_name,
                "profile_picture": profile_picture,
                "nb_items": total_nfts,
            }
        )
        results.append(wallet)
    results = sorted(
        results, key=lambda wallet_dict: wallet_dict["nb_items"], reverse=True
    )
    # return top 9
    return results[:9]
