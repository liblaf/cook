from collections.abc import Mapping
from os import PathLike
from typing import Any

import pydantic


def as_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str | PathLike):
        v = [v]
    return [str(i) for i in v]


class Rule(pydantic.BaseModel):
    name: str
    command: str
    description: str | None = None


class Recipe(pydantic.BaseModel):
    # build
    outputs: list[str] = []
    rule: str | Rule
    inputs: list[str] = []
    implicit: list[str] = []
    order_only: list[str] = []
    variables: dict[str, list[str]] = {}
    implicit_outputs: list[str] = []

    @pydantic.field_validator(
        "outputs", "inputs", "implicit", "order_only", "implicit_outputs", mode="before"
    )
    @classmethod
    def as_list(cls, v: Any) -> list[str]:
        return as_list(v)

    @pydantic.field_validator("variables", mode="before")
    @classmethod
    def as_dict(cls, v: Any) -> dict[str, list[str]]:
        if v is None:
            return {}
        if isinstance(v, Mapping):
            return {str(k): as_list(v) for k, v in v.items()}
        return {}
