"""The nfts crud module"""

from odmantic.session import (
    AIOSession,
)
from typing import (
    Any,
    Dict,
    Optional,
)
from xrpl.asyncio.account import (
    get_account_info,
)
from xrpl.asyncio.clients import (
    AsyncJsonRpcClient,
)
from xrpl.asyncio.transaction import (
    safe_sign_and_autofill_transaction,
    send_reliable_submission,
)
from xrpl.models.requests import (
    AccountNFTs,
)
from xrpl.models.transactions import (
    AccountSetFlag,
    NFTokenBurn,
    NFTokenCreateOffer,
    NFTokenCreateOfferFlag,
    NFTokenMint,
)
from xrpl.utils import (
    hex_to_str,
    str_to_hex,
)
from xrpl.wallet import (
    Wallet,
)

from app.auth import (
    crud as auth_crud,
)
from app.config import (
    settings,
)
from app.wallets import (
    models as wallets_models,
)


async def mint_nft_token(
    classic_address: str,
    meta_data: str,
    session: AIOSession,
    has_offer: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    A method to fetch wallet info.

    Args:
        classic_address (str) : A wallet classic address.
        meta_data (str) : A comma separated string of values that represents the data to be minted.
        session (odmantic.session.AIOSession) : odmantic session object.
        has_offer (bool) : A bool that indicates whether or not the nft has a sell offer.
    Returns:
        Dict[str, Any]: A dict that represents the account info object.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    account_info = await get_account_info(classic_address, client, "validated")
    sequence = account_info.result["account_data"]["Sequence"]
    wallet = await auth_crud.find_existed_wallet(
        classic_address=classic_address, session=session
    )
    wallet = Wallet(sequence=sequence, seed=wallet.seed)
    tx_settings = NFTokenMint(
        account=classic_address,
        nftoken_taxon=0,
        uri=str_to_hex(meta_data),
        flags=AccountSetFlag.ASF_DEFAULT_RIPPLE,  # Enable rippling on this account.
    )
    tx_settings_prepared = await safe_sign_and_autofill_transaction(
        transaction=tx_settings,
        wallet=wallet,
        client=client,
    )
    response = await send_reliable_submission(tx_settings_prepared, client)
    if has_offer:
        # get the recently created token id
        response = await client.request(
            AccountNFTs(
                account=classic_address,
            )
        )
        account_nfts = response.result["account_nfts"]
        nftoken_id = account_nfts[-1]["NFTokenID"]
        # create an offer for that token
        tx_settings = NFTokenCreateOffer(
            account=classic_address,
            amount=meta_data.split(",")[-1],
            nftoken_id=nftoken_id,
            flags=NFTokenCreateOfferFlag.TF_SELL_NFTOKEN,
        )
        tx_settings_prepared = await safe_sign_and_autofill_transaction(
            transaction=tx_settings,
            wallet=wallet,
            client=client,
        )
        response = await send_reliable_submission(tx_settings_prepared, client)
    return response


async def burn_nft_token(
    classic_address: str, nftoken_id: str, session: AIOSession
) -> Dict[str, Any]:
    """
    A method to burn an nft token.

    Args:
        classic_address (str) : A wallet classic address.
        nftoken_id (str) : A token id to be burnt.
        session (odmantic.session.AIOSession) : odmantic session object.
    Returns:
        Dict[str, Any]: A dict that represents the account info object.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    account_info = await get_account_info(classic_address, client, "validated")
    sequence = account_info.result["account_data"]["Sequence"]
    wallet = await auth_crud.find_existed_wallet(
        classic_address=classic_address, session=session
    )
    wallet = Wallet(sequence=sequence, seed=wallet.seed)
    tx_settings = NFTokenBurn(
        account=classic_address,
        nftoken_id=nftoken_id,
    )
    tx_settings_prepared = await safe_sign_and_autofill_transaction(
        transaction=tx_settings,
        wallet=wallet,
        client=client,
    )
    response = await send_reliable_submission(tx_settings_prepared, client)
    return response


async def get_all_nfts(classic_address: str) -> Dict[str, Any]:
    """
    A method to fetch all nfts from the ledger for a given account.

    Args:
        classic_address (str) : A wallet classic address.
    Returns:
        Dict[str, Any]: A dict that represents the account info object.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    results = []
    response = await client.request(
        AccountNFTs(
            account=classic_address,
        )
    )
    account_nfts = response.result["account_nfts"]
    for nft_token in account_nfts:
        nftokens_list = hex_to_str(nft_token["URI"]).split(",")
        if len(nftokens_list) == 4:
            author_avatar, picture, title, price = nftokens_list
            results.append(
                {
                    "id": nft_token["NFTokenID"],
                    "author_avatar": author_avatar,
                    "image_url": picture,
                    "title": title,
                    "price": price,
                }
            )
    return {"status_code": 200, "results": results}


async def get_all_wallets_nfts(session: AIOSession) -> Dict[str, Any]:
    """
    A method to fetch all nfts from the ledger for all accounts.

    Args:
        session (odmantic.session.AIOSession) : odmantic session object.

    Returns:
        Dict[str, Any]: A dict that represents all info about all nfts.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    all_registered_wallets = await session.find(wallets_models.Wallet)
    results = []
    for wallet in all_registered_wallets:
        response = await client.request(
            AccountNFTs(
                account=wallet.classic_address,
            )
        )
        account_nfts = response.result["account_nfts"]
        for nft_token in account_nfts:
            modified_nftokens_list = hex_to_str(nft_token["URI"]).split(",")
            if len(modified_nftokens_list) == 4:
                author_avatar, picture, title, price = modified_nftokens_list
                results.append(
                    {
                        "id": nft_token["NFTokenID"],
                        "author_avatar": author_avatar,
                        "image_url": picture,
                        "title": title,
                        "price": price,
                    }
                )
    return {"status_code": 200, "results": results}
