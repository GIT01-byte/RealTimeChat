from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class RabbitMQMessage(BaseModel, Generic[T]):
    sender: str
    body: T
