"""The wallets schemas module"""

from pydantic import (
    BaseModel,
    Field,
)
from typing import (
    Any,
    Dict,
    Optional,
)


class WalletObjectSchema(BaseModel):
    """
    A Pydantic class that defines the wallet schema for fetching wallet info.
    """

    token: Optional[str] = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey")
    account_info: Dict[str, Any] = Field(
        ...,
        example={
            "Account": "rBtXmAdEYcno9LWRnAGfT9qBxCeDvuVRZo",
            "Balance": "3166000000",
            "Flags": 0,
            "LedgerEntryType": "AccountRoot",
            "OwnerCount": 0,
            "PreviousTxnID": "3AA321338BDE48E79DAC40269A4AAC6A72A6F4FD4C4961EBF6429AE3A278B815",
            "PreviousTxnLgrSeq": 30798857,
            "Sequence": 16233962,
            "index": "FD66EC588B52712DCE74831DCB08B24157DC3198C29A0116AA64D310A58512D7",
        },
    )
    message: str = Field(..., example="A new wallet has been generated successfully!")
    status_code: int = Field(..., example=201)


class WalletTokenObjectSchema(BaseModel):
    """
    A Pydantic class that defines the wallet schema for fetching wallet info.
    """

    wallet: Dict[str, Any] = Field(
        ...,
        example={
            "Account": "rBtXmAdEYcno9LWRnAGfT9qBxCeDvuVRZo",
            "Balance": "3166000000",
            "Flags": 0,
            "LedgerEntryType": "AccountRoot",
            "OwnerCount": 0,
            "PreviousTxnID": "3AA321338BDE48E79DAC40269A4AAC6A72A6F4FD4C4961EBF6429AE3A278B815",
            "PreviousTxnLgrSeq": 30798857,
            "Sequence": 16233962,
            "index": "FD66EC588B52712DCE74831DCB08B24157DC3198C29A0116AA64D310A58512D7",
        },
    )
    status_code: int = Field(..., example=200)
    message: str = Field(..., example="Welcome to Moerphous.")


class WalletInfo(BaseModel):
    """
    A Pydantic class that defines the users schema for the updating user info.
    """

    first_name: str = Field(..., example="First name.")
    bio: str = Field(..., example="Bio.")
