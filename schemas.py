from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=200, examples=["첫 번째 게시글"])
    user_id: int = Field(gt=0, examples=[1])


class PostUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=200, examples=["수정한 제목"])


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    user_id: int
