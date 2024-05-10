import asyncio

from cook import Menu
from cook._typing import StrPath

m = Menu()


def fmt_toml(file: StrPath) -> None:
    file = str(file)
    m.add("fmt-toml", f"fmt-toml:{file}", phony=True)
    m.add(
        f"fmt-toml:{file}",
        file,
        [["toml-sort", "--in-place", "--all", file], ["taplo", "format", file]],
        phony=True,
    )


m.add("default", ["check", "fmt"], phony=True)
m.add("check", None, [["ruff", "check"]], check=False, phony=True)
m.add("fmt", ["fmt-py", "fmt-toml"], phony=True)
m.add("fmt-py", None, [["ruff", "format"]], phony=True)
fmt_toml("pyproject.toml")
fmt_toml("ruff.toml")
asyncio.run(m.cook("default"))
