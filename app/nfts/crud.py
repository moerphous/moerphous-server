"""The nfts crud module"""

from datetime import (
    timedelta,
)
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
    get_account_transactions,
)
from xrpl.asyncio.clients import (
    AsyncJsonRpcClient,
)
from xrpl.asyncio.transaction import (
    safe_sign_and_autofill_transaction,
    send_reliable_submission,
)
from xrpl.asyncio.wallet import (
    generate_faucet_wallet,
)
from xrpl.models.transactions import (
    AccountSetFlag,
    NFTokenBurn,
    NFTokenCreateOffer,
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
from app.utils import (
    jwt,
)
from app.wallets import (
    models as wallets_models,
)


async def create_nft(session: AIOSession) -> Dict[str, Any]:
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
        wallet_instance = wallets_models.Wallet(classic_address=wallet.classic_address)
        await session.save(wallet_instance)

    account_info = await get_account_info(wallet.classic_address, client, "validated")

    return {
        "token": access_token["access_token"],
        "account_info": account_info,
        "message": "A new wallet has been generated successfully!",
        "status_code": 201,
    }


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
        account_info = await get_account_transactions(classic_address, client)
        created_nodes = [
            element["CreatedNode"]["NewFields"]
            for element in account_info[0]["meta"]["AffectedNodes"]
            if "CreatedNode" in element
        ]
        modified_nodes = [
            element["ModifiedNode"]["FinalFields"]
            for element in account_info[0]["meta"]["AffectedNodes"]
            if "ModifiedNode" in element
        ]
        # check if there are NFTokens to fetch meta_data
        if len(modified_nodes) == 1 and not modified_nodes[0].get("NFTokens"):
            modified_nodes = []
        else:
            modified_nodes = [
                element for element in modified_nodes if "NFTokens" in element
            ]
        if len(created_nodes) == 1 and not created_nodes[0].get("NFTokens"):
            created_nodes = []
        else:
            created_nodes = [
                element for element in created_nodes if "NFTokens" in element
            ]
        if len(modified_nodes) > 0 and "NFTokens" in modified_nodes[0]:
            nftoken_id = modified_nodes[0]["NFTokens"][-1]["NFToken"]["NFTokenID"]
        if len(created_nodes) > 0 and "NFTokens" in created_nodes[0]:
            nftoken_id = created_nodes[0]["NFTokens"][-1]["NFToken"]["NFTokenID"]
        # create an offer for that token
        tx_settings = NFTokenCreateOffer(
            account=classic_address,
            amount=meta_data.split(",")[-1],
            nftoken_id=nftoken_id,
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
    account_info = await get_account_transactions(classic_address, client)
    results = []
    created_nodes = [
        element["CreatedNode"]["NewFields"]
        for element in account_info[0]["meta"]["AffectedNodes"]
        if "CreatedNode" in element
    ]
    modified_nodes = [
        element["ModifiedNode"]["FinalFields"]
        for element in account_info[0]["meta"]["AffectedNodes"]
        if "ModifiedNode" in element
    ]
    # check if there are NFTokens to fetch meta_data
    if len(modified_nodes) == 1 and not modified_nodes[0].get("NFTokens"):
        modified_nodes = []
    else:
        modified_nodes = [
            element for element in modified_nodes if "NFTokens" in element
        ]
    if len(created_nodes) == 1 and not created_nodes[0].get("NFTokens"):
        created_nodes = []
    else:
        created_nodes = [element for element in created_nodes if "NFTokens" in element]
    if len(modified_nodes) > 0 and "NFTokens" in modified_nodes[0]:
        for modified_nftoken in modified_nodes[0]["NFTokens"]:
            modified_nftokens_list = hex_to_str(
                modified_nftoken["NFToken"]["URI"]
            ).split(",")
            if len(modified_nftokens_list) == 4:
                author_avatar, picture, title, price = modified_nftokens_list
                results.append(
                    {
                        "id": modified_nftoken["NFToken"]["NFTokenID"],
                        "author_avatar": author_avatar,
                        "image_url": picture,
                        "title": title,
                        "price": price,
                    }
                )

    if len(created_nodes) > 0 and "NFTokens" in created_nodes[0]:
        for created_nftoken in created_nodes[0]["NFTokens"]:
            created_nftokens_list = hex_to_str(created_nftoken["NFToken"]["URI"]).split(
                ","
            )
            if len(created_nftokens_list) == 4:
                author_avatar, picture, title, price = created_nftokens_list
                results.append(
                    {
                        "id": created_nftoken["NFToken"]["NFTokenID"],
                        "author_avatar": author_avatar,
                        "image_url": picture,
                        "title": title,
                        "price": price,
                    }
                )
    return {"status_code": 200, "results": results}


async def get_all_wallets_nfts(session: AIOSession) -> Dict[str, Any]:
    """
    A method to fetch all nfts from the ledger for a given account.

    Args:
        session (odmantic.session.AIOSession) : odmantic session object.

    Returns:
        Dict[str, Any]: A dict that represents all info about all nfts.
    """
    client = AsyncJsonRpcClient(settings().json_rpc_url)
    all_registered_wallets = await session.find(wallets_models.Wallet)
    results = []
    for wallet in all_registered_wallets:
        account_info = await get_account_transactions(wallet.classic_address, client)
        created_nodes = [
            element["CreatedNode"]["NewFields"]
            for element in account_info[0]["meta"]["AffectedNodes"]
            if "CreatedNode" in element
        ]
        modified_nodes = [
            element["ModifiedNode"]["FinalFields"]
            for element in account_info[0]["meta"]["AffectedNodes"]
            if "ModifiedNode" in element
        ]
        # check if there are NFTokens to fetch meta_data
        if len(modified_nodes) == 1 and not modified_nodes[0].get("NFTokens"):
            modified_nodes = []
        else:
            modified_nodes = [
                element for element in modified_nodes if "NFTokens" in element
            ]
        if len(created_nodes) == 1 and not created_nodes[0].get("NFTokens"):
            created_nodes = []
        else:
            created_nodes = [
                element for element in created_nodes if "NFTokens" in element
            ]
        if len(modified_nodes) > 0 and "NFTokens" in modified_nodes[0]:
            for modified_nftoken in modified_nodes[0]["NFTokens"]:
                modified_nftokens_list = hex_to_str(
                    modified_nftoken["NFToken"]["URI"]
                ).split(",")
                if len(modified_nftokens_list) == 4:
                    author_avatar, picture, title, price = modified_nftokens_list
                    results.append(
                        {
                            "id": modified_nftoken["NFToken"]["NFTokenID"],
                            "author_avatar": author_avatar,
                            "image_url": picture,
                            "title": title,
                            "price": price,
                        }
                    )

        if len(created_nodes) > 0 and "NFTokens" in created_nodes[0]:
            for created_nftoken in created_nodes[0]["NFTokens"]:
                created_nftokens_list = hex_to_str(
                    created_nftoken["NFToken"]["URI"]
                ).split(",")
                if len(created_nftokens_list) == 4:
                    author_avatar, picture, title, price = created_nftokens_list
                    results.append(
                        {
                            "id": created_nftoken["NFToken"]["NFTokenID"],
                            "author_avatar": author_avatar,
                            "image_url": picture,
                            "title": title,
                            "price": price,
                        }
                    )
    return {"status_code": 200, "results": results}
