from typing import Set, TypedDict, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, field


class OutputType(Enum):
    DATACLASS = "dataclass"
    TYPEDDICT = "TypedDict"


class SimpleField(TypedDict, total=False):
    name: str
    type: str
    default: str


class Record(TypedDict):
    name: str
    type: str
    doc: Optional[str]
    fields: List[SimpleField]


class AvroEnum(TypedDict):
    name: str
    type: str
    symbols: List[str]
    doc: Optional[str]


@dataclass
class Collector:
    record: Union[Record, AvroEnum]
    typing: Set[str] = field(default_factory=set)
    schemas: Set[str] = field(default_factory=set)
    dataclass: Set[str] = field(default_factory=set)
    lines: List[str] = field(default_factory=list)
    lines_with_default: List[str] = field(default_factory=list)
