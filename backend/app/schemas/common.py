
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(ORMBase):
    criado_em: datetime
    atualizado_em: datetime
