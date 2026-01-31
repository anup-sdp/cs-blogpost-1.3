# schemas.py 
# pydantic models for request and response validation. automatic validation via type hints
# django equivalent: forms.py and serializers.py in DRF

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
# BaseModel: abstract foundation class that enables type-driven data validation, serialization, and documentation generation.
# Validation: checks if incoming data matches your schema, Incoming (Request)
# Serialization: transformation of Python objects into a format that can be transmitted (typically JSON), Outgoing (Response)

class UserBase(BaseModel): 
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    image_file: str | None
    image_path: str


class UserPrivate(UserPublic):
    email: EmailStr


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    image_file: str | None = Field(default=None, min_length=1, max_length=200)
    

class Token(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    user_id: int  # TEMPORARY


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date_posted: datetime
    author: UserPublic
