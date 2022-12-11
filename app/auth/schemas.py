"""Auth Schemas module."""

from pydantic import (
    BaseModel,
    Field,
)


class WalletLoginSchema(BaseModel):
    """
    A Pydantic class that defines the user schema for logging in.
    """

    access_token: str = Field(..., example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9")
    status_code: int = Field(
        ...,
        example=200,
    )


class Token(BaseModel):
    """
    A Pydantic class that defines the Token schema.
    """

    access_token: str = Field(
        ..., example="Token value(e.g. 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9')"
    )


class TokenData(BaseModel):
    """
    A Pydantic class that defines a Token schema to return the email address.
    """

    classic_address: str = Field(..., example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9")


class ResponseSchema(BaseModel):
    """
    A Pydantic class that defines a Response schema object.
    """

    status_code: int = Field(
        ...,
        example=400,
    )
    message: str = Field(
        ...,
        example="A message to indicate that the request was not successful!",
    )
