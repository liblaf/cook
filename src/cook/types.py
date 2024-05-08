from collections.abc import Sequence
from os import PathLike
from typing import Any, TypeAlias

StrPath: TypeAlias = str | PathLike[str]
StrPathList: TypeAlias = StrPath | Sequence[StrPath]


def is_sequence(obj: Any) -> bool:
    """Check if an object is a sequence or not.

    Args:
        obj: Any object type to be checked

    Returns:
        is_sequence: True if object is sequence
    """
    seq: bool = (not hasattr(obj, "strip") and hasattr(obj, "__getitem__")) or hasattr(
        obj,
        "__iter__",
    )

    # check to make sure it is not a set, string, or dictionary
    return seq and all(not isinstance(obj, i) for i in (dict, set, str))
