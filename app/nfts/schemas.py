"""The nfts schemas module"""

from pydantic import (
    BaseModel,
    Field,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)


class NFTObjectSchema(BaseModel):
    """
    A Pydantic class that defines the wallet schema for fetching wallet info.
    """

    picture: str = Field(..., example="IPFS url of the NFT image.")
    title: str = Field(..., example="Your NFT title.")
    price: str = Field(..., example="Your NFT price in XRP.")


class NFTBase64ObjectSchema(BaseModel):
    """
    A Pydantic class that defines the wallet schema for fetching wallet info.
    """

    picture: str = Field(..., example="Base64 image string.")
    author_avatar: str = Field(..., example="Owner profile picture.")
    title: str = Field(..., example="Your NFT title.")
    price: str = Field(..., example="Your NFT price in XRP.")


class ResponseSchema(BaseModel):
    """
    A Pydantic class that defines the wallet schema for fetching wallet info.
    """

    status_code: int = Field(..., example=200)
    results: List[Optional[Dict[str, Any]]] = Field(
        ..., example="Owner profile picture."
    )


class UploadImageResponseSchema(BaseModel):
    """
    A Pydantic class that defines the wallet schema for fetching wallet info.
    """

    status_code: int = Field(..., example=200)
    url: str = Field(..., example="IPFS URL of the image.")
