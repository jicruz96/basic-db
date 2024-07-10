from ._meta import TableCache as TableCache, TableMeta as TableMeta
from easydatamodel.model import Model
from easydatastore.column import ColumnInfo as ColumnInfo
from typing import Any, Callable, Literal, Self, Sequence, overload

class Table(Model[ColumnInfo], metaclass=TableMeta):
    __field_class__ = ColumnInfo
    __cache__: TableCache[Self]
    def __init__(self, **kwargs: Any) -> None: ...
    @classmethod
    def delete(cls, instance_or_instances: Self | Sequence[Self]) -> None: ...
    @classmethod
    def all(cls) -> Sequence[Self]: ...
    @classmethod
    def filter(cls, filter_func: Callable[[Self], bool] | None = None, *, error_if_not_found: bool = False, **kwargs: Any) -> Sequence[Self]: ...
    @overload
    @classmethod
    def get(cls, pk: Any, error_if_not_found: Literal[True]) -> Self: ...
    @overload
    @classmethod
    def get(cls, pk: Any, error_if_not_found: Literal[False]) -> Self | None: ...
    @overload
    @classmethod
    def get(cls, pk: Any) -> Self: ...
