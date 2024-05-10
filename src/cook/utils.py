import pathlib
from collections.abc import Mapping
from os import PathLike
from typing import Any, TypeVar

from cook._typing import StrPath

C = TypeVar("C", bound=Mapping[str, Any])


def as_dict(**kwargs: Any | None) -> dict[str, Any]:
    result: dict[str, str] = {}
    for k, v in kwargs.items():
        if v is not None:
            result[k] = str(v)
    return result


def as_path(v: Any, cwd: StrPath | None = None) -> pathlib.Path:
    p = pathlib.Path(v)
    if p.is_absolute():
        return p
    if cwd is not None:
        return pathlib.Path(cwd) / p
    return p


def as_str_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str | PathLike):
        return [str(v)]
    return [str(i) for i in v]


def merge_dict(*ctx: Mapping[str, Any] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for c in ctx:
        if c is not None:
            result.update(c)
    return result


def mtime(v: Any, cwd: StrPath | None = None) -> float:
    path: pathlib.Path = as_path(v, cwd)
    if path.exists():
        return path.stat().st_mtime
    return 0.0
