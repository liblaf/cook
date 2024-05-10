# pyright: reportTypedDictNotRequiredAccess=none
from __future__ import annotations

import shlex
import sys
from os import PathLike
from typing import TYPE_CHECKING, Any, Unpack

import rich
import sh

from cook import utils
from cook.recipe import _abc

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence

    from cook._typing import StrPath


class Exec(_abc.Recipe):
    _args: list[str]
    _kwargs: dict[str, str]

    def __init__(
        self,
        *args: StrPath,
        # Recipe Context
        _auto_deps: bool | None = None,
        _check: bool | None = None,
        _cwd: pathlib.Path | None = None,
        _echo: bool | None = None,
        # Controlling Output
        **kwargs: Any,
    ) -> None:
        ctx: _abc.RecipeContext = utils.as_dict(
            auto_deps=_auto_deps, check=_check, cwd=_cwd, echo=_echo
        )  # pyright: ignore [reportAssignmentType]
        super().__init__(**ctx)
        self._args = [str(arg) for arg in args]
        self._kwargs = {k: str(v) for k, v in kwargs.items()}

    @property
    def args(self) -> list[str]:
        args: list[str] = self._args.copy()
        args += [f"--{k}={v}" for k, v in self._kwargs.items()]
        return args

    def _auto_deps(self) -> list[str]:
        deps: list[str] = []
        for arg in self._args:
            if arg.startswith("-"):
                continue
            deps.append(arg)
        deps += self._kwargs.values()
        return deps

    def _echo(self) -> None:
        console: rich.console.Console = rich.get_console()
        console.print("+ " + shlex.join(self.args), highlight=True)

    async def _call(self, **kwargs: Unpack[_abc.RecipeContext]) -> None:
        ctx: _abc.RecipeContext = utils.merge_dict(
            _abc.DEFAULT_CONTEXT, kwargs, self.ctx
        )  # pyright: ignore [reportAssignmentType]
        cmd = sh.Command(self._args[0])
        await cmd(
            *self._args[1:],
            **self._kwargs,
            _out=sys.stdout,
            _err=sys.stderr,
            _async=True,
            _cwd=ctx["cwd"],
        )  # pyright: ignore [reportGeneralTypeIssues]


def as_recipe(r: StrPath | Sequence[StrPath] | _abc.Recipe) -> _abc.Recipe:
    if isinstance(r, _abc.Recipe):
        return r
    if isinstance(r, str | PathLike):
        return Exec(r)
    return Exec(*r)
