
# `easydatastore` - Create type-safe, in-memory datastores 

## Requirements
* Python 3.11+

## Install

```bash
pip install easydatastore
```

## Usage

If you want to prototype a web application quickly and just need a way to validate your mock data, you can use `easydatastore` to create an in-memory datastore for your models, directly out of the box.

### Features:

* In-memory tables for your models with `easydatastore.Table`, with a familiar pydantic-flavored syntax and ORM-like API.
* Enforce uniqueness constraints with `Column(unique=True)`
* Use indexing for faster lookups with `Column(index=True)`
* IDE-friendly type hints ensure your coding experience is type-safe.

### Example

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
