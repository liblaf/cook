from collections.abc import Iterable
from os import PathLike

import cook
import cook.text
from cook.context import Context
from cook.recipe import Recipe
from cook.typing import Args, StrPath


class Rule:
    context: Context
    targets: list[StrPath]
    deps: list[StrPath]
    recipes: list[Recipe]

    def __init__(
        self,
        targets: Args,
        deps: Args | None = None,
        recipes: Iterable[Recipe | Args] | None = None,
    ) -> None:
        self.targets = cook.text.make_sequence(targets)
        self.deps = cook.text.make_sequence(deps) if deps else []
        self.recipes = [Recipe(r) for r in recipes] if recipes else []
        for recipe in self.recipes:
            for arg in recipe.args:
                if isinstance(arg, PathLike) and arg not in self.deps:
                    self.deps.append(arg)

    def __str__(self) -> str:
        return self.dump()

    def dump(self) -> str:
        result: str = cook.text.join_targets(self.targets)
        result += ":"
        if self.deps:
            result += " " + cook.text.join_targets(self.deps)
        result += "\n"
        for recipe in self.recipes:
            result += "\t" + recipe.dump() + "\n"
        return result
