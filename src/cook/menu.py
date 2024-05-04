from collections.abc import Iterable

from cook.recipe import Recipe
from cook.rule import Rule
from cook.typing import Args


class Menu:
    rules: list[Rule]

    def __init__(self) -> None:
        self.rules = []

    def __str__(self) -> str:
        return self.dump()

    def add(
        self,
        targets: Args,
        deps: Args | None = None,
        recipes: Iterable[Recipe | Args] | None = None,
    ) -> None:
        self.rules.append(Rule(targets, deps, recipes))

    def dump(self) -> str:
        result: str = "\n".join([rule.dump() for rule in self.rules])
        return result
