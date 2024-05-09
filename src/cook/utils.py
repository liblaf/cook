from collections.abc import Mapping
from os import PathLike
from typing import Any, TypeVar

C = TypeVar("C", bound=Mapping[str, Any])


def as_str_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str | PathLike):
        return [str(v)]
    return [str(i) for i in v]


def merge_dict(*ctx: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for c in ctx:
        result.update(c)
    return result
