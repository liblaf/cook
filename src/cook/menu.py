import asyncio
from collections.abc import Sequence
from typing import Unpack

import cook.utils
from cook import recipe as _recipe
from cook import rule as _rule
from cook._typing import StrPath, StrPathList


class MenuContext(_rule.RuleContext, total=False):
    jobs: int


class MenuContextTotal(_rule.RuleContextTotal, total=True):
    jobs: int


DEFAULT_CONTEXT = MenuContextTotal(**_rule.DEFAULT_CONTEXT, jobs=1)


class Menu:
    ctx: MenuContextTotal
    sem: asyncio.Semaphore
    rules: list[_rule.Rule]

    def __init__(self, **kwargs: Unpack[MenuContext]) -> None:
        self.ctx = DEFAULT_CONTEXT | kwargs  # pyright: ignore [reportOperatorIssue]
        self.sem = asyncio.Semaphore(self.ctx["jobs"])
        self.rules = []

    def __contains__(self, target: str) -> bool:
        return any(target in rule.targets for rule in self.rules)

    def __getitem__(self, target: str) -> _rule.Rule:
        for rule in self.rules:
            if target in rule.targets:
                return rule
        raise KeyError(target)

    def add(
        self,
        targets: StrPathList,
        dependencies: StrPathList | None = None,
        recipes: Sequence[StrPath | StrPathList | _recipe.Recipe] | None = None,
        **kwargs: Unpack[_rule.RuleContext],
    ) -> None:
        ctx: MenuContext = self.ctx | kwargs  # pyright: ignore [reportOperatorIssue]
        rule = _rule.Rule(targets, dependencies, recipes, **ctx)  # pyright: ignore [reportArgumentType]
        self.rules.append(rule)

    async def cook(self, *targets: StrPathList) -> None:
        target_list: list[str] = cook.utils.as_str_list(targets)
        await asyncio.gather(*[self._cook(t) for t in target_list])

    async def _cook(self, target: str) -> None:
        await self._cook_rule(self[target])

    async def _cook_rule(self, rule: _rule.Rule) -> None:
        deps: list[str] = self._gather_deps(rule)
        await asyncio.gather(*[self._cook(d) for d in deps])
        async with self.sem:
            for r in rule.recipes:
                await self._cook_recipe(r)

    async def _cook_recipe(self, recipe: _recipe.Recipe) -> None:
        await recipe()

    def _gather_deps(self, rule: _rule.Rule) -> list[str]:
        deps: list[str] = rule.deps
        deps += [d for d in rule.auto_deps() if d in self]
        return list(dict.fromkeys(deps))
