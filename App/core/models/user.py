from dataclasses import dataclass


@dataclass
class User:
    api_key: str

    def __hash__(self) -> int:
        return hash(self.api_key)
