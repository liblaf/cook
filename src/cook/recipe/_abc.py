# pyright: reportTypedDictNotRequiredAccess=none
from __future__ import annotations

import abc
from typing import TYPE_CHECKING, TypedDict, Unpack

from loguru import logger

from cook import utils

if TYPE_CHECKING:
    import pathlib


class RecipeContext(TypedDict, total=False):
    auto_deps: bool
    check: bool
    cwd: pathlib.Path | None
    echo: bool


DEFAULT_CONTEXT = RecipeContext(
    auto_deps=True,
    check=True,
    cwd=None,
    echo=True,
)


class Recipe(abc.ABC):
    ctx: RecipeContext

    def __init__(self, **kwargs: Unpack[RecipeContext]) -> None:
        self.ctx = utils.merge_dict(kwargs)  # pyright: ignore [reportAttributeAccessIssue]

    async def __call__(self, **kwargs: Unpack[RecipeContext]) -> None:
        await self.cook(**kwargs)

    def auto_deps(self, **kwargs: Unpack[RecipeContext]) -> list[str]:
        ctx: RecipeContext = utils.merge_dict(DEFAULT_CONTEXT, kwargs, self.ctx)  # pyright: ignore [reportAssignmentType]
        if not ctx["auto_deps"]:
            return []
        return self._auto_deps()

    async def cook(self, **kwargs: Unpack[RecipeContext]) -> None:
        ctx: RecipeContext = utils.merge_dict(DEFAULT_CONTEXT, kwargs, self.ctx)  # pyright: ignore [reportAssignmentType]
        if ctx["echo"]:
            self._echo()
        try:
            await self._call(**ctx)
        except Exception as e:
            logger.exception(e)
            if ctx["check"]:
                raise

    @abc.abstractmethod
    def _echo(self) -> None: ...

    def _auto_deps(self) -> list[str]:
        return []

    @abc.abstractmethod
    async def _call(self, **kwargs: Unpack[RecipeContext]) -> None: ...
