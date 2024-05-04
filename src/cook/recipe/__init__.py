import shlex

import cook.text
from cook.typing import Args, StrPath


class Recipe:
    args: list[StrPath]
    echo: bool = True
    ignore_error: bool = False

    def __init__(self, args: "Recipe | Args") -> None:
        if isinstance(args, Recipe):
            self.args = args.args
            self.echo = args.echo
            self.ignore_error = args.ignore_error
        else:
            self.args = cook.text.make_sequence(args)

    def __str__(self) -> str:
        return self.dump()

    def dump(self) -> str:
        result: str = ""
        if not self.echo:
            result += "@"
        if self.ignore_error:
            result += "-"
        result += shlex.join([str(arg) for arg in self.args])
        return result
