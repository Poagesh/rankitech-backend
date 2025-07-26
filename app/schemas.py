from pydantic import BaseModel

class JDInput(BaseModel):
    title: str
    content: str

class ProfileInput(BaseModel):
    name: str
    content: str
