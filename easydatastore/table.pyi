from ._meta import TableCache as TableCache, TableMeta as TableMeta
from easydatamodel.model import _GenericModel
from easydatastore.column import ColumnInfo as ColumnInfo
from typing import Any, Callable, Literal, Self, Sequence, overload

class Table(_GenericModel[ColumnInfo], metaclass=TableMeta):
    __field_class__ = ColumnInfo
    __cache__: TableCache['Table']
    def __init__(self, **kwargs: Any) -> None: ...
    @classmethod
    def delete(cls, instance_or_instances: Self | Sequence[Self]) -> None: ...
    @classmethod
    def all(cls) -> Sequence['Table']: ...
    @classmethod
    def filter(cls, filter_func: Callable[[Table], bool] | None = None, *, error_if_not_found: bool = False, **kwargs: Any) -> Sequence['Table']: ...
    @overload
    @classmethod
    def get(cls, pk: Any, error_if_not_found: Literal[True]) -> Table: ...
    @overload
    @classmethod
    def get(cls, pk: Any, error_if_not_found: Literal[False]) -> Table | None: ...
    @overload
    @classmethod
    def get(cls, pk: Any) -> Table: ...
