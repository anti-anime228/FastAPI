from pydantic import BaseModel, EmailStr


class CreateUser(BaseModel):
    username: str
    password: str
    email: EmailStr
    age: int


class UpdateUser(BaseModel):
    email: EmailStr
    age: int


class CreateSecret(BaseModel):
    content: str
    created_at: str


class UpdateSecret(BaseModel):
    content: str
