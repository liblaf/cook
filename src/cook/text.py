from collections.abc import Iterable
from typing import Any

from cook.typing import StrPath, is_sequence


def make_sequence(obj: Any) -> list[StrPath]:
    if is_sequence(obj):
        return list(obj)
    return [obj]


def join_targets(args: Iterable[StrPath]) -> str:
    return " ".join([str(arg) for arg in args])
