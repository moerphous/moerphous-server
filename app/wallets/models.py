"""The users models module"""

from datetime import (
    datetime,
)
from odmantic import (
    Field,
    Model,
)
from typing import (
    Optional,
)


class Wallet(Model):
    """
    The Wallet model

    Args:
        Model (odmantic.Model): Odmantic base model.
    """

    classic_address: str = Field(index=True)
    seed: str = Field(index=True)
    wallet_status: int = Field(default=1)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # {
    #   id: 4,
    #   title: "NFT",
    #   url: "./images/author.jpeg",
    #   status: "has_offers",
    #   likes: "4",
    #   price: "3",
    #   bid_url: "",
    #   bid: "1",
    #   max_bid: "20",
    #   author_url: "./images/author.jpeg",
    #   author_avatar: "./images/author.jpeg",
    #   image_url: "./images/background1.jpg",
    # },


__all__ = [
    "Wallet",
]
