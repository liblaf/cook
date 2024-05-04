import dataclasses


@dataclasses.dataclass(kw_only=True)
class Context:
    auto_deps: bool = True
