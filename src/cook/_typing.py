from collections.abc import Sequence
from os import PathLike
from typing import TypeAlias

StrPath: TypeAlias = str | PathLike[str]
StrPathList: TypeAlias = StrPath | Sequence[StrPath]
