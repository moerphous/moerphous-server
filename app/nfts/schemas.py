"""The nfts schemas module"""

from pydantic import (
    BaseModel,
    Field,
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
