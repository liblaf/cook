# pyright: reportTypedDictNotRequiredAccess=none
from collections.abc import Sequence
from typing import Unpack

from cook import recipe as _r
from cook import utils
from cook._typing import StrPath, StrPathList


class RuleContext(_r.RecipeContext, total=False): ...


DEFAULT_CONTEXT = RuleContext(**_r.DEFAULT_CONTEXT)


class Rule:
    ctx: RuleContext
    targets: list[str]
    deps: list[str]
    recipes: list[_r.Recipe]

    def __init__(
        self,
        targets: StrPathList,
        deps: StrPathList | None = None,
        recipes: Sequence[StrPath | StrPathList | _r.Recipe] | None = None,
        **kwargs: Unpack[RuleContext],
    ) -> None:
        self.ctx = utils.merge_dict(kwargs)  # pyright: ignore [reportAttributeAccessIssue]
        self.targets = utils.as_str_list(targets)
        self.deps = utils.as_str_list(deps)
        self.recipes = [_r.as_recipe(r) for r in recipes] if recipes else []

    def auto_deps(self, **kwargs: Unpack[RuleContext]) -> list[str]:
        ctx: RuleContext = utils.merge_dict(DEFAULT_CONTEXT, kwargs, self.ctx)  # pyright: ignore [reportAssignmentType]
        if not ctx["auto_deps"]:
            return []
        auto_deps: list[str] = []
        for r in self.recipes:
            auto_deps += r.auto_deps(**ctx)
        return list(dict.fromkeys(auto_deps))

    async def cook(self, **kwargs: Unpack[RuleContext]) -> None:
        ctx: RuleContext = utils.merge_dict(DEFAULT_CONTEXT, kwargs, self.ctx)  # pyright: ignore [reportAssignmentType]
        for r in self.recipes:
            await r.cook(**ctx)
