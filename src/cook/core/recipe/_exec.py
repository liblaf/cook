import asyncio
import shlex
import subprocess
import sys
from collections.abc import Sequence
from os import PathLike
from typing import TextIO, TypedDict

import rich.console

from cook import utils
from cook._typing import StrPath, StrPathList
from cook.core.recipe import _abc


class SpecialKwargs(TypedDict, total=False):
    _out: StrPath | TextIO
    _err: StrPath | TextIO
    _long_sep: str
    _long_prefix: str


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
        _long_sep: str = "=",
        _long_prefix: str = "--",
        # Kwargs
        **kwargs: StrPath,
    ) -> None:
        ctx: _abc.RecipeContext = utils.as_dict(
            auto_deps=_auto_deps, check=_check, cwd=_cwd, echo=_echo
        )  # pyright: ignore [reportAssignmentType]
        super().__init__(**ctx)
        self._args = utils.as_str_list(args)
        self._kwargs = utils.as_str_dict(**kwargs)
        self._special_kwargs = utils.as_dict(
            _out=_out, _err=_err, _long_sep=_long_sep, _long_prefix=_long_prefix
        )  # pyright: ignore [reportAttributeAccessIssue]

    @property
    def args(self) -> list[str]:
        args: list[str] = self._args.copy()
        for k, v in self._kwargs.items():
            arg: str = self._special_kwargs["_long_prefix"] + k
            if (sep := self._special_kwargs["_long_sep"]).isspace():
                args += [arg, v]
            else:
                args.append(arg + sep + v)
        return args

    async def _cook(self) -> None:
        # TODO: controlling output
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
            *self.args
        )
        returncode: int = await proc.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, self.args)

    def _echo(self) -> None:
        console: rich.console.Console = rich.get_console()
        console.print("+ " + shlex.join(self.args), style="bright_green")

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
