import asyncio
import shlex
import subprocess
from collections.abc import Sequence
from os import PathLike
from typing import Unpack

import rich

from cook._typing import StrPath
from cook.recipe import _abc


class Exec(_abc.Recipe):
    args: list[str]

    def __init__(self, *args: StrPath, **kwargs: Unpack[_abc.RecipeContext]) -> None:
        super().__init__(**kwargs)
        self.args = [str(arg) for arg in args]

    def _auto_deps(self) -> list[str]:
        return self.args[1:]

    def _echo(self) -> None:
        console: rich.console.Console = rich.get_console()
        console.print("+ " + shlex.join(self.args), style="bright_green")

    async def _call(self, **kwargs: Unpack[_abc.RecipeContext]) -> None:
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
            *self.args
        )
        returncode: int = await proc.wait()
        if returncode:
            raise subprocess.CalledProcessError(returncode, self.args)


def as_recipe(
    r: StrPath | Sequence[StrPath] | _abc.Recipe, **kwargs: Unpack[_abc.RecipeContext]
) -> _abc.Recipe:
    if isinstance(r, _abc.Recipe):
        return r
    if isinstance(r, str | PathLike):
        return Exec(r, **kwargs)
    return Exec(*r, **kwargs)
