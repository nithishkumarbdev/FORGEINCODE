from pydantic import BaseModel, Field


class SubmitRequest(BaseModel):
    code: str = Field("", max_length=20000)


class MentorRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    code: str = Field("", max_length=20000)
