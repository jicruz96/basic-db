from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Generic, Sequence, TypeVar, Union, cast

from easydatamodel.field import ModelFieldMap

from easydatastore.column import ColumnInfo

from .exceptions import DuplicateUniqueFieldValueError, ModelNotFoundError, NoPrimaryKeyError

if TYPE_CHECKING:
    from .table import Table

from easydatamodel._meta import ModelMeta

T = TypeVar("T", bound="Table")


class TableMeta(ModelMeta):

    def __new__(mcs, class_name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type["Table"]:
        cls = cast(type["Table"], super().__new__(mcs, class_name, bases, namespace))  # type: ignore
        cls.__cache__ = TableCache(cls)
        return cls

    @property
    def columns(cls) -> list[ColumnInfo]:
        return list(cast(ModelFieldMap[ColumnInfo], cls.__fields_map__).values())  # type: ignore

    @property
    def pk(cls) -> ColumnInfo | None:
        for field in cls.columns:
            if field.primary_key:
                return field
        return None


class TableCache(Generic[T]):
    """Cache for instances of a Table subclass.

    The cache uses index-based and unique-value-based dictionaries to optimize filtering and retrieval of instances.
    """

    model: type[T]
    all: list[T]

    def __init__(self, model: type[T]):
        self.model = model
        self._unique_field_cache = UniqueFieldCache(model)
        self._index_field_cache = IndexFieldCache(model)
        self.all = []

    def add_model(self, obj: T) -> None:
        if not isinstance(obj, self.model):
            raise TypeError(f"Can only cache instances of {self.model.__name__}.")

        self._unique_field_cache.add_model(obj)
        self._index_field_cache.add_model(obj)
        self.all.append(obj)

    def update_model(self, obj: T, field: ColumnInfo, value: Any) -> None:
        if not isinstance(obj, self.model):
            raise TypeError(f"Can only cache instances of {self.model.__name__}.")
        if obj not in self.all:
            raise ValueError(f"{obj} is not in the cache.")
        if field.unique:
            self._unique_field_cache.update_model(obj, field, value)
        if field.index:
            self._index_field_cache.update_model(obj, field, value)

    def delete(self, instance_or_instances: Union[T, Sequence[T]]) -> None:
        if not isinstance(instance_or_instances, Sequence):
            instance_or_instances = [instance_or_instances]
        for instance in instance_or_instances:
            if not isinstance(instance, self.model):
                raise TypeError(f"Can only delete instances of {self.model.__name__}.")
            self.all.remove(instance)
            for field_name, cache in self._unique_field_cache.items():
                value = getattr(instance, field_name)
                if value is not None:
                    del cache[value]
            for field_name, cache in self._index_field_cache.items():
                value = getattr(instance, field_name)
                cache[value].remove(instance)

    def get(self, pk_value: Any, error_if_not_found: bool) -> Union[T, None]:
        pk = self.model.pk
        if pk is None:
            raise NoPrimaryKeyError(f"{self.model.__name__} does not have a primary key.")
        value = self._unique_field_cache[pk.name].get(pk_value)
        if not value:
            if error_if_not_found:
                raise ModelNotFoundError(f"{self.model.__name__} with {pk.name}={pk_value} not found.")
            return None
        return value

    def filter(
        self, filter_func: Callable[[T], bool] | None = None, *, error_if_not_found: bool = False, **kwargs: Any
    ) -> list[T]:
        # Unique fields are the fastest to filter by, so filter by them if possible
        unique_field_kwargs: list[str] = list(filter(lambda k: k in self._unique_field_cache, kwargs))
        # If there are any unique fields in kwargs, use the unique field cache only
        if unique_field_kwargs:
            column_name = unique_field_kwargs[0]
            obj = self._unique_field_cache.find(column_name=column_name, value=kwargs.pop(column_name))
            objects = [obj] if obj else []
        else:
            # Otherwise, filter first by index fields (if any), then by other fields (if any)
            index_field_kwargs: dict[str, Any] = {
                k: kwargs.pop(k) for k in list(kwargs.keys()) if k in self._index_field_cache
            }
            if index_field_kwargs:
                objects = self._index_field_cache.filter(**index_field_kwargs)
            else:
                objects = self.all

        def _filter(obj: T) -> bool:
            matches_all_kwargs = all(getattr(obj, name) == value for name, value in kwargs.items())
            passes_user_filter = filter_func is None or filter_func(obj)
            return matches_all_kwargs and passes_user_filter

        objects = list(filter(_filter, objects))
        if not objects and error_if_not_found:
            raise ModelNotFoundError(f"{self.model.__name__} with values {kwargs} not found.")
        return objects


class UniqueFieldCache(dict[str, dict[Any, T]]):
    def __init__(self, model: type[T]):
        self.model = model
        for column in model.columns:
            if column.unique:
                self[column.name] = {}

    def add_model(self, obj: T) -> None:
        if not isinstance(obj, self.model):
            raise TypeError(f"Can only cache instances of {self.model.__name__}.")
        errors: dict[str, str] = {}
        for field_name, cache in self.items():
            value = getattr(obj, field_name)
            if value is None:
                if self.model.pk is not None and field_name == self.model.pk.name:
                    errors[field_name] = f"Primary key '{field_name}' cannot be None."
                continue
            existing = cache.get(value)
            if existing is not None:
                errors[field_name] = f"The value of {field_name}={value} already exists in {existing}."
        if errors:
            raise DuplicateUniqueFieldValueError(errors)

        for field_name, cache in self.items():
            value = getattr(obj, field_name)
            if value is not None:
                cache[value] = obj

    def update_model(self, obj: T, field: ColumnInfo, value: Any) -> None:
        if field.primary_key and value is None:
            raise ValueError(f"Primary key '{field.name}' cannot be None.")
        if value is not None and obj.filter(error_if_not_found=False, **{field.name: value}):
            raise ValueError(f"Value '{value}' for field '{field.name}' is not unique.")
        del self[field.name][getattr(obj, field.name)]
        self[field.name][value] = obj

    def find(self, column_name: str, value: str) -> T | None:
        if column_name not in self:
            raise ValueError(f"{self.model.__name__}.{column_name} is not a unique field.")
        return self[column_name].get(value)


class IndexFieldCache(dict[str, dict[str, list[T]]]):
    def __init__(self, model: type[T]):
        self.model = model
        for column in model.columns:
            if column.index:
                self[column.name] = defaultdict(list[T])

    def add_model(self, obj: T) -> None:
        if not isinstance(obj, self.model):
            raise TypeError(f"Can only cache instances of {self.model.__name__}.")
        for field_name, cache in self.items():
            cache[getattr(obj, field_name)].append(obj)

    def update_model(self, obj: T, field: ColumnInfo, value: Any) -> None:
        self[field.name][getattr(obj, field.name)].remove(obj)
        self[field.name][value].append(obj)

    def filter(self, **kwargs: Any) -> list[T]:
        invalid_kwargs = set(kwargs.keys()) - set(col.name for col in self.model.columns)
        if invalid_kwargs:
            raise TypeError(f"{self.model.__name__} does not have fields named {invalid_kwargs}.")

        kwargs_items = list(kwargs.items())

        def _get_validated_kwarg_value() -> tuple[str, Any]:
            column_name, value = kwargs_items.pop()
            if column_name not in self:
                raise ValueError(f"{self.model.__name__}.{column_name} is not an index field.")
            return column_name, value

        column_name, value = _get_validated_kwarg_value()
        models = self[column_name].get(value, [])
        while kwargs_items and models:
            column_name, value = _get_validated_kwarg_value()
            models = [m for m in models if getattr(m, column_name) == value]
        return models
