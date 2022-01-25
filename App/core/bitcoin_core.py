from App.core.requests import CreateWalletRequest, RegisterUserRequest
from App.core.responses import CreateWalletResponse, RegisterUserResponse


class BitcoinCore:
    def register_user(self, request: RegisterUserRequest) -> RegisterUserResponse:
        return RegisterUserResponse(api_key="blabla", status_code=500)

    def create_wallet(self, request: CreateWalletRequest) -> CreateWalletResponse:
        pass
