import shlex
import sys
from collections.abc import Sequence
from os import PathLike
from typing import TextIO, TypedDict

import rich.console
import sh

from cook import utils
from cook._typing import StrPath, StrPathList
from cook.core.recipe import _abc


class SpecialKwargs(TypedDict, total=False):
    _out: StrPath | TextIO
    _err: StrPath | TextIO


class Exec(_abc.Recipe):
    _args: list[str]
    _kwargs: dict[str, str]
    _special_kwargs: SpecialKwargs

    def __init__(
        self,
        *args: StrPath,
        # Recipe Context
        _auto_deps: bool | None = None,
        _check: bool | None = None,
        _cwd: StrPath | None = None,
        _echo: StrPath | None = None,
        # Special Kwargs
        _out: StrPath | TextIO | None = sys.stdout,
        _err: StrPath | TextIO | None = sys.stderr,
        # Kwargs
        **kwargs: StrPath,
    ) -> None:
        ctx: _abc.RecipeContext = utils.as_dict(
            auto_deps=_auto_deps, check=_check, cwd=_cwd, echo=_echo
        )  # pyright: ignore [reportAssignmentType]
        super().__init__(**ctx)
        self._args = utils.as_str_list(args)
        self._kwargs = utils.as_str_dict(**kwargs)
        self._special_kwargs = utils.as_dict(_out=_out, _err=_err)  # pyright: ignore [reportAttributeAccessIssue]

    async def _cook(self) -> None:
        c = sh.Command(self._args[0])
        await c(self._args[1:], **self._kwargs, **self._special_kwargs, _async=True)  # pyright: ignore [reportGeneralTypeIssues]

    def _echo(self) -> None:
        console: rich.console.Console = rich.get_console()
        console.print(shlex.join(self._args), style="bright_green")

    def _files(self) -> StrPathList:
        files: list[str] = []
        for arg in self._args:
            if arg.startswith("-"):
                continue
            files.append(arg)
        files.extend(self._kwargs.values())
        return files


def as_recipe(r: StrPath | Sequence[StrPath] | _abc.Recipe) -> _abc.Recipe:
    if isinstance(r, _abc.Recipe):
        return r
    if isinstance(r, str | PathLike):
        return Exec(r)
    return Exec(*r)
