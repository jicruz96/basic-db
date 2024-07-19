from __future__ import annotations

from typing import Any, Callable, Literal, Optional, Self, Sequence, overload

from easydatamodel.model import _GenericModel  # type: ignore

from easydatastore.column import ColumnInfo

from ._meta import TableCache, TableMeta


class Table(_GenericModel[ColumnInfo], metaclass=TableMeta):
    """Base class for easydatastore tables.

    ### Usage

    ```python
    import easydatastore.exceptions
    from easydatastore import Column, Table


    class Person(Table):
        name: str = Column(primary_key=True)
        email: str | None = Column(unique=True, default=None)
        family_name: str
        age: int


    Person(name="Snap", family_name="Krispies", email="snap@example.com", age=92)
    Person(name="Crackle", family_name="Krispies", age=92)
    Person(name="Pop", family_name="Krispies", age=92)
    Person(name="Tony", family_name="Tiger", email="tony@example.com", age=72)
    Person(name="Cap'n", family_name="Crunch", age=53)

    # retrieve an instance from the table using the .get() method and a primary key value
    tony = Person.get("Tony")
    print(tony)  # Person(name='Tony', email=None, family_name='Tiger')

    # or query your table using the .filter() method
    print([person.name for person in Person.filter(family_name="Krispies")])  # ["Snap", "Crackle", "Pop"]
    print([person.name for person in Person.filter(lambda person: person.age < 90)])  # ["Tony", "Cap'n"]

    # delete instances from the table with the .delete() method
    Person.delete(Person.get("Crackle"))
    print([person.name for person in Person.all()])  # ["Snap", "Pop", "Tony"]

    # easydatastore will validate uniqueness for you... these operations will raise exceptions:
    try:
        tony.email = Person.get("Snap").email
    except ValueError as e:
        print(e.args[0])  # ValueError: Value 'snap@example.com' for field 'email' is not unique

    try:
        Person(name="Snap", family_name="Rice", age=1)
    except easydatastore.exceptions.DuplicateUniqueFieldValueError as e:
        print(e.args[0])  # DuplicateUniqueFieldValueError

    ```
    """

    __field_class__ = ColumnInfo
    __cache__: TableCache["Table"]  # type: ignore

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.__cache__.add_model(self)

    @classmethod
    def delete(cls, instance_or_instances: Self | Sequence[Self]) -> None:
        """Delete one or more instances from the cache."""
        cls.__cache__.delete(instance_or_instances)

    @classmethod
    def all(cls) -> Sequence["Table"]:
        """Retrieve all instances of the model."""
        return cls.__cache__.all

    @classmethod
    def filter(
        cls, filter_func: Callable[["Table"], bool] | None = None, *, error_if_not_found: bool = False, **kwargs: Any
    ) -> Sequence["Table"]:
        """Filter instances, using either a filter function or keyword arguments.

        Args:
            error_if_not_found: Optional. Whether to raise an error if no instances are found. Defaults to False.

        Returns:
            A list of instances that match the filters.

        Raises:
            ModelNotFoundError: If `error_if_not_found` is True and no instances are found.

        ### Example

        ```python
        from easydatastore import Table

        class Person(Table):
            name: str
            age: int

        adults = Person.filter(lambda person: person.age >= 18)
        ```
        """
        return cls.__cache__.filter(filter_func, error_if_not_found=error_if_not_found, **kwargs)

    @overload
    @classmethod
    def get(cls, pk: Any, error_if_not_found: Literal[True]) -> "Table": ...  # noqa: E704

    @overload
    @classmethod
    def get(cls, pk: Any, error_if_not_found: Literal[False]) -> Optional["Table"]: ...  # noqa: E704

    @overload
    @classmethod
    def get(cls, pk: Any) -> "Table": ...  # noqa: E704

    @classmethod
    def get(cls, pk: Any, error_if_not_found: bool = True) -> Optional["Table"]:
        return cls.__cache__.get(pk, error_if_not_found=error_if_not_found)
