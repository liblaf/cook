import io
import pathlib
from collections.abc import Mapping
from typing import TextIO

import cook
import cook.ninja
import cook.ninja.syntax
import cook.recipe
from cook.types import StrPath, StrPathList


class Menu:
    recipes: list[cook.recipe.Recipe]
    _default: list[str]

    def __init__(self) -> None:
        self.recipes = []
        self._default = []

    @property
    def targets(self) -> list[str]:
        return [output for recipe in self.recipes for output in recipe.outputs]

    def add(
        self,
        outputs: StrPathList,
        rule: str | None = None,
        command: str | None = None,
        description: str | None = None,
        inputs: StrPathList | None = None,
        implicit: StrPathList | None = None,
        order_only: StrPathList | None = None,
        variables: Mapping[str, StrPathList] | None = None,
        implicit_outputs: StrPathList | None = None,
    ) -> None:
        rule_: str | cook.recipe.Rule
        if command is None:
            rule_ = rule or "phony"
        else:
            outputs_escaped: list[str] = cook.recipe.as_list(outputs)
            outputs_escaped: list[str] = [
                cook.ninja.syntax.escape_path(x) for x in outputs_escaped
            ]
            name: str = " ".join(outputs_escaped)
            rule_ = cook.recipe.Rule(
                name=name, command=command, description=description
            )
        recipe = cook.recipe.Recipe(
            outputs=outputs,  # pyright: ignore [reportArgumentType]
            rule=rule_,
            inputs=inputs,  # pyright: ignore [reportArgumentType]
            implicit=implicit,  # pyright: ignore [reportArgumentType]
            order_only=order_only,  # pyright: ignore [reportArgumentType]
            variables=variables,  # pyright: ignore [reportArgumentType]
            implicit_outputs=implicit_outputs,  # pyright: ignore [reportArgumentType]
        )
        self.recipes.append(recipe)

    def default(self, default: StrPathList) -> None:
        self._default += cook.recipe.as_list(default)

    def auto(self) -> None:
        targets: list[str] = self.targets
        for recipe in self.recipes:
            for values in recipe.variables.values():
                for v in values:
                    if all(
                        (
                            (v in targets),
                            (v not in recipe.outputs),
                            (v not in recipe.inputs),
                            (v not in recipe.implicit),
                            (v not in recipe.order_only),
                            (v not in recipe.implicit_outputs),
                        )
                    ):
                        recipe.implicit.append(v)

    def save(self, file: TextIO | StrPath = "build.ninja") -> None:
        output: io.TextIOWrapper
        if isinstance(file, TextIO | io.TextIOWrapper):
            output = file  # pyright: ignore [reportAssignmentType]
        else:
            self.add(
                outputs=file,
                command="python $in",
                description="Generate Ninja",
                inputs=__file__,
            )
            output = pathlib.Path(file).open("w")  # noqa: SIM115
        writer = cook.ninja.syntax.Writer(output=output)
        for recipe in self.recipes:
            rule_name: str
            if isinstance(recipe.rule, cook.recipe.Rule):
                rule_name = recipe.rule.name
                writer.rule(
                    name=recipe.rule.name,
                    command=recipe.rule.command,
                    description=recipe.rule.description,
                )
            else:
                rule_name = recipe.rule
            writer.build(
                outputs=recipe.outputs,
                rule=rule_name,
                inputs=recipe.inputs,
                implicit=recipe.implicit,
                order_only=recipe.order_only,
                variables=recipe.variables,  # pyright: ignore [reportArgumentType]
                implicit_outputs=recipe.implicit_outputs,
            )
        if self._default:
            writer.default(self._default)
        writer.close()
