# pyright: reportTypedDictNotRequiredAccess=false
import asyncio
import pathlib
from collections.abc import Coroutine, Sequence
from typing import Unpack

from loguru import logger

from cook import utils
from cook._typing import StrPath, StrPathList
from cook.core import recipe as _recipe
from cook.core import rule as _rule


class MenuContext(_rule.RuleContext, total=False):
    jobs: int


DEFAULT_CONTEXT = MenuContext(**_rule.DEFAULT_CONTEXT, jobs=1)


class Menu:
    ctx: MenuContext
    cooked: set[str]
    phony_targets: set[str]
    rules: dict[str, _rule.Rule]
    sem: asyncio.Semaphore

    def __init__(self, **kwargs: Unpack[MenuContext]) -> None:
        self.ctx = kwargs
        self.phony_targets = set()
        self.rules = {}

    @property
    def targets(self) -> list[str]:
        return list(self.rules.keys())

    def add(
        self,
        targets: StrPathList,
        deps: StrPathList | None = None,
        recipes: Sequence[StrPathList | _recipe.Recipe] | None = None,
        *,
        phony: bool = False,
        **kwargs: Unpack[_rule.RuleContext],
    ) -> None:
        targets = utils.as_str_list(targets)
        rule = _rule.Rule(targets, deps, recipes, **kwargs)
        for t in targets:
            if t in self.rules:
                logger.warning("overriding recipe for target '{}'", t)
            self.rules[t] = rule
        if phony:
            self.phony_targets.update(targets)
        else:
            self.phony_targets.difference_update(targets)

    def auto_deps(self) -> None:
        for r in self.rules.values():
            r.auto_deps(self.targets)

    def context(self, **kwargs: Unpack[MenuContext]) -> None:
        self.ctx = utils.merge_dict(DEFAULT_CONTEXT, kwargs, self.ctx)  # pyright: ignore [reportAttributeAccessIssue]
        self.sem = asyncio.Semaphore(self.ctx["jobs"])
        for r in self.rules.values():
            r.context(**self.ctx)

    async def cook(self, *targets: StrPath, **kwargs: Unpack[MenuContext]) -> None:
        self.context(**kwargs)
        self.auto_deps()
        self.cooked = set()
        target_list: list[str] = utils.as_str_list(targets)
        jobs: list[Coroutine[None, None, None]] = []
        for t in target_list:
            if self.up_to_date(t):
                logger.info("'{}' is up to date.", t)
            else:
                jobs.append(self._cook_target(t))
        await asyncio.gather(*jobs)

    async def _cook_target(
        self, target: str, needed_by: list[str] | None = None
    ) -> None:
        if self.up_to_date(target):
            return
        needed_by = utils.as_list(needed_by).copy()
        if target in needed_by:
            logger.warning(
                "Circular '{}' <- '{}' dependency dropped.", target, needed_by[-1]
            )
            return
        rule: _rule.Rule | None = self.rules.get(target)
        if rule is None:
            msg: str = f"No rule to cook target '{target}'."
            raise ValueError(msg)
        needed_by.append(target)
        await asyncio.gather(*[self._cook_target(d, needed_by) for d in rule.deps])
        await self._cook_rule(rule)

    async def _cook_rule(self, rule: _rule.Rule) -> None:
        mtime: dict[str, float] = {
            t: utils.mtime(t, rule.ctx["cwd"]) for t in rule.targets
        }
        async with self.sem:
            await rule.cook()
        for t in rule.targets:
            if not self.is_phony(t) and utils.mtime(t, rule.ctx["cwd"]) <= mtime[t]:
                logger.warning("Target '{}' is not updated.", t)
        self.cooked.update(rule.targets)

    def is_phony(self, target: StrPath) -> bool:
        return str(target) in self.targets

    def up_to_date(self, target: StrPath) -> bool:
        target = str(target)
        if target in self.cooked:
            return True
        if self.is_phony(target):
            return False
        target_path: pathlib.Path = utils.as_path(target, self.ctx["cwd"])
        if not target_path.exists():
            return False
        if rule := self.rules.get(target):
            target_mtime: float = target_path.stat().st_mtime
            for d in rule.deps:
                if self.is_phony(d) or not self.up_to_date(d):
                    return False
                dep_time: float = utils.mtime(d, self.ctx["cwd"])
                if target_mtime < dep_time:
                    return False
        return True
