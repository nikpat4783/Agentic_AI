from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DomainOut(BaseModel):
    id: str
    name: str
    description: str
    example_questions: list[str]


class ResearchRequest(BaseModel):
    domain_id: str
    model: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1, max_length=2000)
    session_id: str
