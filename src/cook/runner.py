# pyright: reportTypedDictNotRequiredAccess=none
from __future__ import annotations

import asyncio
import itertools
import pathlib
from typing import TYPE_CHECKING, TypedDict, Unpack

import networkx as nx
from loguru import logger

from cook import utils

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from cook._typing import StrPath
    from cook.recipe import Recipe
    from cook.rule import Rule, RuleContext


class RunnerContext(TypedDict, total=False):
    jobs: int


DEFAULT_CONTEXT = RunnerContext(jobs=1)


class Runner:
    ctx: RunnerContext
    cooked: set[str]
    phony_targets: set[str]
    rules: dict[str, Rule]
    sem: asyncio.Semaphore

    def __init__(
        self,
        phony_targets: set[str],
        rules: dict[str, Rule],
        **kwargs: Unpack[RunnerContext],
    ) -> None:
        self.ctx = utils.merge_dict(DEFAULT_CONTEXT, kwargs)  # pyright: ignore [reportAttributeAccessIssue]
        self.cooked = set()
        self.phony_targets = phony_targets
        self.rules = rules
        self.sem = asyncio.Semaphore(self.ctx["jobs"])

    def check_cyclic_deps(self) -> bool:
        graph = nx.DiGraph()
        for r in self.rules.values():
            graph.add_edges_from(list(itertools.product(r.targets, r.deps)))
        return nx.is_directed_acyclic_graph(graph)

    async def cook(self, *targets: StrPath) -> None:
        target_list: list[str] = utils.as_str_list(targets)
        jobs: list[Coroutine[None, None, None]] = []
        for t in target_list:
            if self.up_to_date(t):
                logger.info(f"'{t}' is up to date.")
            else:
                jobs.append(self.cook_target(t))
        await asyncio.gather(*jobs)

    async def cook_target(
        self, target: str, needed_by: list[str] | None = None
    ) -> None:
        if self.up_to_date(target):
            return
        needed_by = needed_by.copy() if needed_by is not None else []
        if target in needed_by:
            msg: str = f"Circular '{target}' <- '{needed_by[-1]}' dependency dropped."
            logger.warning(
                "Circular '{}' <- '{} dependency dropped.", target, needed_by[-1]
            )
            return
        rule: Rule | None = self.rules.get(target)
        if rule is None:
            msg: str = f"No rule to cook target '{target}'."
            raise ValueError(msg)
        needed_by.append(target)
        await asyncio.gather(*[self.cook_target(d, needed_by) for d in rule.deps])
        await self.cook_rule(rule)

    async def cook_rule(self, rule: Rule) -> None:
        ctx: RuleContext = utils.merge_dict(self.ctx, rule.ctx)  # pyright: ignore [reportAssignmentType]
        mtime: dict[str, float] = {t: utils.mtime(t, ctx["cwd"]) for t in rule.targets}
        async with self.sem:
            for r in rule.recipes:
                await self.cook_recipe(r)
        for t in rule.targets:
            if not self.is_phony(t) and utils.mtime(t, ctx["cwd"]) <= mtime[t]:
                logger.warning("Target '{}' is not updated.", t)

    async def cook_recipe(self, recipe: Recipe) -> None:
        await recipe.cook(**self.ctx)

    def is_phony(self, target: str) -> bool:
        return target in self.phony_targets

    def up_to_date(self, target: str) -> bool:
        if target in self.cooked:
            return True
        if self.is_phony(target):
            return False
        target_path: pathlib.Path = pathlib.Path(target)
        if not target_path.exists():
            return False
        if rule := self.rules.get(target):
            target_mtime: float = target_path.stat().st_mtime
            for d in rule.deps:
                if self.is_phony(d) or not self.up_to_date(d):
                    return False
                dep_mtime: float = pathlib.Path(d).stat().st_mtime
                if target_mtime < dep_mtime:
                    return False
        return True
