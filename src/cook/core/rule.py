import functools
import operator
from collections.abc import Sequence
from typing import Unpack

from cook import utils
from cook._typing import StrPathList
from cook.core import recipe as _recipe


class RuleContext(_recipe.RecipeContext, total=False): ...


DEFAULT_CONTEXT = RuleContext(**_recipe.DEFAULT_CONTEXT)


class Rule:
    ctx: RuleContext
    targets: list[str]
    deps: list[str]
    recipes: list[_recipe.Recipe]

    def __init__(
        self,
        targets: StrPathList,
        deps: StrPathList | None = None,
        recipes: Sequence[StrPathList | _recipe.Recipe] | None = None,
        **kwargs: Unpack[RuleContext],
    ) -> None:
        self.ctx = kwargs
        self.targets = utils.as_str_list(targets)
        self.deps = utils.as_str_list(deps)
        self.recipes = [_recipe.as_recipe(r) for r in utils.as_list(recipes)]

    def auto_deps(self, targets: StrPathList) -> None:
        deps: list[str] = self.files()
        targets = utils.as_str_list(targets)
        deps = [f for f in deps if f in targets]
        deps = list(dict.fromkeys(self.deps + deps))
        self.deps = deps

    def context(self, **kwargs: Unpack[RuleContext]) -> None:
        self.ctx = utils.merge_dict(DEFAULT_CONTEXT, kwargs, self.ctx)  # pyright: ignore [reportAttributeAccessIssue]
        for r in self.recipes:
            r.context(**self.ctx)

    async def cook(self) -> None:
        for r in self.recipes:
            await r.cook()

    def files(self) -> list[str]:
        files: list[str] = functools.reduce(
            operator.iconcat, (r.files() for r in self.recipes), []
        )
        files = [f for f in files if f not in self.targets]
        return list(dict.fromkeys(files))
