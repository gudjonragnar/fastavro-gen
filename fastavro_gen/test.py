from typing import TypedDict


class A(TypedDict, total=False):
    a: int
    b: str


a1: A = {"a": 1}
a2: A = {"b": "asdf"}

a1["b"] = 2