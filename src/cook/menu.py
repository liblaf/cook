# pyright: reportTypedDictNotRequiredAccess=none
import copy
from collections.abc import Sequence
from typing import Unpack

from loguru import logger

from cook import utils
from cook._typing import StrPath, StrPathList
from cook.recipe import Recipe
from cook.rule import DEFAULT_CONTEXT as RULE_DEFAULT_CONTEXT
from cook.rule import Rule, RuleContext
from cook.runner import DEFAULT_CONTEXT as RUNNER_DEFAULT_CONTEXT
from cook.runner import Runner, RunnerContext


class MenuContext(RuleContext, RunnerContext, total=False): ...


DEFAULT_CONTEXT = MenuContext(**RULE_DEFAULT_CONTEXT, **RUNNER_DEFAULT_CONTEXT)


class Menu:
    ctx: MenuContext
    phony_targets: set[str]
    rules: dict[str, Rule]

    def __init__(self, **kwargs: Unpack[MenuContext]) -> None:
        self.ctx = kwargs
        self.phony_targets = set()
        self.rules = {}

    def __contains__(self, target: str) -> bool:
        return target in self.rules

    def __getitem__(self, target: str) -> Rule:
        return self.rules[target]

    def add(
        self,
        targets: StrPathList,
        deps: StrPathList | None = None,
        recipes: Sequence[StrPath | StrPathList | Recipe] | None = None,
        *,
        phony: bool = False,
        **kwargs: Unpack[RuleContext],
    ) -> None:
        targets = utils.as_str_list(targets)
        rule = Rule(targets, deps, recipes, **kwargs)
        for t in targets:
            if t in self:
                logger.warning(f"ignoring old rule for target '{t}'")
            if phony:
                self.phony_targets.add(t)
            self.rules[t] = rule

    async def cook(self, *targets: StrPath, **kwargs: Unpack[MenuContext]) -> None:
        ctx: MenuContext = DEFAULT_CONTEXT | kwargs | self.ctx
        runner = Runner(self.phony_targets, self._build_rules(**kwargs), **ctx)
        await runner.cook(*targets)

    def _build_rules(self, **kwargs: Unpack[MenuContext]) -> dict[str, Rule]:
        rules: dict[str, Rule] = copy.deepcopy(self.rules)
        for k, v in rules.items():
            rules[k] = self._gather_deps(v, **kwargs)
        return rules

    def _gather_deps(self, rule: Rule, **kwargs: Unpack[MenuContext]) -> Rule:
        result: Rule = copy.deepcopy(rule)
        for d in rule.auto_deps(**kwargs):
            if d in self:
                result.deps.append(d)
        result.deps = list(dict.fromkeys(result.deps))
        return result
