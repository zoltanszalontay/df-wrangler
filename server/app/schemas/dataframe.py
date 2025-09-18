from pydantic import BaseModel

class DataFrameSchema(BaseModel):
    name: str
    data: dict
