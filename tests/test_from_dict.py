from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from tests.utils import roundtrip


@dataclass
class Inner:
    a: str


def test_primitives():
    @dataclass
    class Test:
        a: int = 1
        b: str = "default string"
        c: bool = True
        d: float = 2.0

    test = Test()
    assert test == roundtrip(test)


def test_optional_and_union():
    @dataclass
    class Test:
        a: Optional[int]
        b: Union[int, str]

    test1 = Test(1, 2)
    test2 = Test(None, "3")

    assert test1 == roundtrip(test1)
    assert test2 == roundtrip(test2)


def test_lists():
    @dataclass
    class Test:
        a: List[int]
        b: List[Inner]

    test = Test([1, 2, 3, 4], [Inner("first"), Inner("second")])
    assert test == roundtrip(test)


def test_map():
    @dataclass
    class Test:
        a: Dict[str, int]
        b: Dict[str, Union[str, bool]]

    test = Test(
        {"k1": 1, "k2": 2},
        {"k1": "v1", "k2": True},
    )
    assert test == roundtrip(test)
