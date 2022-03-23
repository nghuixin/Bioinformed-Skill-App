from random import randint
from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from app.db.base_class import Base


@as_declarative()
class Base:
    id: Any
    __name__: str
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class test_Base:
    id: Any = randint(1, 100)
    __name__: str = "TESTNAME"

    def __tablename__(cls) -> str:

        assert cls.__tablename__() == "tableclass"

