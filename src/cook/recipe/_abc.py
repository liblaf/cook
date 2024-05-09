import abc
import pathlib
from typing import TypedDict, Unpack

from loguru import logger


class RecipeContext(TypedDict, total=False):
    auto_deps: bool
    check: bool
    cwd: pathlib.Path
    echo: bool


class RecipeContextTotal(TypedDict, total=True):
    auto_deps: bool
    check: bool
    cwd: pathlib.Path
    echo: bool


DEFAULT_CONTEXT = RecipeContextTotal(
    auto_deps=True, check=True, cwd=pathlib.Path.cwd(), echo=True
)


class Recipe(abc.ABC):
    ctx: RecipeContext

    def __init__(self, **kwargs: Unpack[RecipeContext]) -> None:
        self.ctx = kwargs

    async def __call__(self, **kwargs: Unpack[RecipeContext]) -> None:
        ctx: RecipeContextTotal = DEFAULT_CONTEXT | self.ctx | kwargs  # pyright: ignore [reportOperatorIssue]
        if ctx["echo"]:
            self._echo()
        try:
            await self._call(**kwargs)
        except Exception as e:
            logger.exception(e)
            if ctx["check"]:
                raise

    def auto_deps(self, **kwargs: Unpack[RecipeContext]) -> list[str]:
        ctx: RecipeContextTotal = DEFAULT_CONTEXT | self.ctx | kwargs  # pyright: ignore [reportOperatorIssue]
        if not ctx["auto_deps"]:
            return []
        return self._auto_deps()

    @abc.abstractmethod
    def _echo(self) -> None: ...

    def _auto_deps(self) -> list[str]:
        return []

    @abc.abstractmethod
    async def _call(self, **kwargs: Unpack[RecipeContext]) -> None: ...
