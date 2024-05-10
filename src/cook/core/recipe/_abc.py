# pyright: reportTypedDictNotRequiredAccess=false
import abc
from typing import TypedDict, Unpack

from loguru import logger

from cook import utils
from cook._typing import StrPath, StrPathList


class RecipeContext(TypedDict, total=False):
    auto_deps: bool
    check: bool
    cwd: StrPath
    echo: bool


DEFAULT_CONTEXT = RecipeContext(auto_deps=True, check=True, cwd=".", echo=True)


class Recipe(abc.ABC):
    ctx: RecipeContext

    def __init__(self, **kwargs: Unpack[RecipeContext]) -> None:
        self.ctx = kwargs

    def context(self, **kwargs: Unpack[RecipeContext]) -> None:
        self.ctx = utils.merge_dict(DEFAULT_CONTEXT, kwargs, self.ctx)  # pyright: ignore [reportAttributeAccessIssue]

    async def cook(self) -> None:
        if self.ctx["echo"]:
            self._echo()
        try:
            await self._cook()
        except Exception as e:
            logger.error(e)
            if self.ctx["check"]:
                raise

    def files(self) -> list[str]:
        if not self.ctx["auto_deps"]:
            return []
        return utils.as_str_list(self._files())

    @abc.abstractmethod
    async def _cook(self) -> None: ...

    @abc.abstractmethod
    def _echo(self) -> None: ...

    @abc.abstractmethod
    def _files(self) -> StrPathList: ...
