from dataclasses import dataclass


@dataclass
class RegisterUserRequest:
    pass


@dataclass
class CreateWalletRequest:
    api_key: str
