from pydantic import BaseModel


class LetterBase(BaseModel):
    name: str
    address: str
    address2: str
    city: str
    state: str
    zip: str
    code: str
    date: str
    expiry: str
    app: str
    url: str


class LetterCreate(LetterBase):
    pass


class Letter(LetterBase):
    id: int

    class Config:
        orm_mode = True
