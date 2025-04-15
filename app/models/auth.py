from pydantic import BaseModel


class KeyIdentifications(BaseModel):
    id: int
    api_key: str
    service_name: str
    is_active: bool

    class Config:
        from_attributes = True
