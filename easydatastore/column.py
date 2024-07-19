from __future__ import annotations

import re
import typing
from collections.abc import Callable, Mapping

from easydatamodel._typing import UNASSIGNED, UnassignedType
from easydatamodel.exceptions import InvalidFieldError
from easydatamodel.field import FieldInfo

CLASS_VAR_PATTERN = re.compile(r"(typing\.)?ClassVar(\[(?P<inner_type>.*)\])?")

if typing.TYPE_CHECKING:
    from .table import Table


def Column(
    default: typing.Any = UNASSIGNED,
    default_factory: Callable[[], typing.Any] | UnassignedType = UNASSIGNED,
    type: typing.Any = UNASSIGNED,
    init: typing.Optional[bool] = None,
    choices: typing.Optional[list[typing.Any]] = None,
    repr: bool = True,
    compare: bool = True,
    metadata: typing.Optional[Mapping[typing.Any, typing.Any]] = None,
    primary_key: bool = False,
    unique: bool = False,
    index: bool = False,
) -> typing.Any:
    """Provide specific configuration information for an easydatamodel column.

    Attributes:
        default: default column value.
        default_factory: 0-argument function called to initialize a column's value.
        type: the column's type. If not provided, the type will be inferred from type hints.
        init: if True, the column will be a parameter to the class's __init__() function. If False, it is up to the
            caller to set a default or a default_factory.
        primary_key: if True, the column will be the primary key for the model.
        unique: if True, the column value must be unique across all instances of the model.
        index: if True, the column will be a table index for the model.
        choices: If provided, allowed values for the column.
        repr: if True, the column will be included in the object's string representation.
        compare: if True, the column will be considered when comparing objects to the model (i.e. '==' and '!=')
        metadata: bespoke column metadata.

    Returns:
        A `FieldInfo` object. Return type is `Any` so it plays nicely with your type checker.

    Raises:
        InvalidFieldError:
            - if default and default_factory are both set.
            - if init is False and default or default_factory is not set.
            - if a column's type cannot be determined.
    """
    return ColumnInfo(
        default=default,
        default_factory=default_factory,
        type=type,
        init=init,
        primary_key=primary_key,
        unique=unique,
        index=index,
        choices=choices,
        repr=repr,
        compare=compare,
        metadata=metadata,
    )


class ColumnInfo(FieldInfo):
    """Represents a column in a easydatastore model.

    Attributes:
        default: default column value.
        default_factory: 0-argument function called to initialize a column's value.
        type: the column's type. If not provided, the type will be inferred from type hints.
        init: if True, the column will be a parameter to the class's __init__() function. If False, it is up to the
            caller to set a default or a default_factory.
        primary_key: if True, the column will be the primary key for the model.
        unique: if True, the column value must be unique across all instances of the model.
        index: if True, the column will be a table index for the model.
        choices: If provided, allowed values for the column.
        repr: if True, the column will be included in the object's string representation.
        compare: if True, the column will be considered when comparing objects to the model (i.e. '==' and '!=')
        metadata: bespoke column metadata.
        name: the name of the column. This will usually be set by the metaclass unless you know what you're doing.

    Raises:
        InvalidFieldError:
            - if default and default_factory are both set.
            - if init is False and default or default_factory is not set.
            - if a column's type cannot be determined.
    """

    def __init__(
        self,
        *,
        default: typing.Any = UNASSIGNED,
        default_factory: Callable[[], typing.Any] | UnassignedType = UNASSIGNED,
        type: typing.Any = UNASSIGNED,
        const: bool = False,
        init: typing.Optional[bool] = None,
        primary_key: bool = False,
        unique: bool = False,
        index: bool = False,
        choices: typing.Optional[list[typing.Any]] = None,
        repr: bool = True,
        compare: bool = True,
        metadata: typing.Optional[Mapping[typing.Any, typing.Any]] = None,
        name: str | UnassignedType[str] = UNASSIGNED,
    ) -> None:
        super().__init__(
            name=name,
            default=default,
            default_factory=default_factory,
            type=type,
            const=const,
            init=init,
            repr=repr,
            compare=compare,
            metadata=metadata,
            choices=choices,
        )
        self.__primary_key = primary_key
        self.__unique = unique
        self.__index = index

    def __repr__(self) -> str:
        _repr = super().__repr__()[:-1]
        _repr += f" primary_key={self.primary_key} unique={self.unique} index={self.index}>"
        return _repr

    @property
    def primary_key(self) -> bool:
        return self.__primary_key

    @property
    def unique(self) -> bool:
        return self.__unique is True or self.primary_key is True

    @property
    def index(self) -> bool:
        return self.__index is True

    @property
    def owner(self) -> type["Table"] | None:
        return typing.cast(type["Table"], super().owner)

    def __set__(self, instance: "Table", value: typing.Any) -> None:  # type: ignore
        assert self.owner is not None and isinstance(instance, self.owner)
        if self.name in instance.__dict__:
            self.owner.__cache__.update_model(instance, self, value)  # type: ignore
        super().__set__(instance, value)  # type: ignore

    def copy(self) -> ColumnInfo:
        """Return a copy of the field without its owner and name values set so it can be used in another class."""
        return self.__class__(
            type=self.type,
            default=self.default,
            default_factory=self.default_factory,
            const=self.const,
            init=self.init,
            repr=self.repr,
            compare=self.compare,
            metadata=self.metadata,
            unique=self.unique,
            index=self.index,
            choices=self.choices,
            primary_key=self.primary_key,
        )

    def _validate_and_set_classvar_field(self):
        if self.primary_key is True:
            raise InvalidFieldError(f"Field '{self.name}' cannot be a primary key and a class field.")
        if self.unique is True:
            raise InvalidFieldError(f"Field '{self.name}' cannot be unique and a class field.")
        if self.index is True:
            raise InvalidFieldError(f"Field '{self.name}' cannot be indexed and a class field.")
        super()._validate_and_set_classvar_field()
