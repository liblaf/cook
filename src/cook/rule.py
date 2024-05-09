from collections.abc import Sequence
from typing import Unpack

import cook.recipe
import cook.utils
from cook._typing import StrPath, StrPathList


class RuleContext(cook.recipe.RecipeContext, total=False):
    phony: bool


class RuleContextTotal(cook.recipe.RecipeContextTotal, total=True):
    phony: bool


DEFAULT_CONTEXT = RuleContextTotal(**cook.recipe.DEFAULT_CONTEXT, phony=False)


class Rule:
    ctx: RuleContext
    targets: list[str]
    deps: list[str]
    recipes: list[cook.recipe.Recipe]

    def __init__(
        self,
        targets: StrPathList,
        deps: StrPathList | None = None,
        recipes: Sequence[StrPath | StrPathList | cook.recipe.Recipe] | None = None,
        **kwargs: Unpack[RuleContext],
    ) -> None:
        self.ctx = kwargs
        self.targets = cook.utils.as_str_list(targets)
        self.deps = cook.utils.as_str_list(deps)
        self.recipes = (
            [cook.recipe.as_recipe(r, **kwargs) for r in recipes] if recipes else []
        )

    def auto_deps(self, **kwargs: Unpack[RuleContext]) -> list[str]:
        ctx: RuleContextTotal = DEFAULT_CONTEXT | self.ctx | kwargs  # pyright: ignore [reportOperatorIssue]
        if not ctx["auto_deps"]:
            return []
        auto_deps: list[str] = []
        for r in self.recipes:
            auto_deps += r.auto_deps(**kwargs)
        return list(dict.fromkeys(auto_deps))
