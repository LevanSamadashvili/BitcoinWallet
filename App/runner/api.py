from typing import Any

from fastapi import Body, Depends, FastAPI, Response

from App.core import status
from App.core.bitcoin_core import BitcoinCore
from App.core.requests import RegisterUserRequest
from App.core.responses import CreateWalletResponse, RegisterUserResponse

app = FastAPI()


def validate_api_key(body: dict[str, Any]) -> bool:
    return "api_key" in body


def get_core() -> BitcoinCore:
    return BitcoinCore()


@app.post(
    "/users",
    responses={
        status.USER_REGISTRATION_ERROR: {"description": "User registration error"},
        status.USER_CREATED_SUCCESSFULLY: {"description": "User created successfully"},
    },
)
def register_user(
    response: Response, bitcoin_core: BitcoinCore = Depends(get_core)
) -> RegisterUserResponse:
    """
    - Registers user
    - Returns API key that can authenticate all subsequent requests for this user
    """

    register_user_response = bitcoin_core.register_user(RegisterUserRequest())
    response.status_code = register_user_response.status_code
    return register_user_response


@app.post("/wallets")
def create_wallet(
    body: dict[str, Any] = Body(..., example={"api_key": "120341024"}),
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> CreateWalletResponse:
    """
     - Requires API key
     - Create BTC wallet
     - Deposits 1 BTC (or 100000000 satoshis) automatically to the new
    wallet
     - User may register up to 3 wallets
     - Returns wallet address and balance in BTC and USD
    """

    # response = bitcoin_core.create_wallet(CreateWalletRequest(api_key=api_key))
    return CreateWalletResponse(
        "Bad Request, Order_Complete_At missing", 0.5, 0.5, status_code=400
    )


@app.get("/wallets/{address}")
def get_balance(
    body: dict[str, Any], address: str, bitcoin_core: BitcoinCore = Depends(get_core)
) -> dict[str, str]:
    """
    - Requires API key
    - Returns wallet address and balance in BTC and USD
    """

    return {}


@app.post("/transactions")
def make_transaction(
    body: dict[str, Any], bitcoin_core: BitcoinCore = Depends(get_core)
) -> dict[str, str]:
    """
    - Requires API key
    - Makes a transaction from one wallet to another
    - Transaction is free if the same user is the owner of both wallets
    - System takes a 1.5% (of the transferred amount) fee for transfers
    to the foreign wallets
    """

    return {}


@app.get("/transactions")
def get_transactions(
    body: dict[str, Any], bitcoin_core: BitcoinCore = Depends(get_core)
) -> dict[str, str]:
    """
    - Requires API key
    - Returns list of transactions
    """

    return {}


@app.get("/wallets/{address}/transactions")
def get_wallet_transactions(
    body: dict[str, Any], address: str, bitcoin_core: BitcoinCore = Depends(get_core)
) -> dict[str, str]:
    """
    - Requires API key
    - returns transactions related to the wallet
    """

    return {}


@app.get("/statistics")
def get_statistics(
    body: dict[str, Any], bitcoin_core: BitcoinCore = Depends(get_core)
) -> dict[str, str]:
    """
    - Requires pre-set (hard coded) Admin API key
    - Returns the total number of transactions and platform profit
    """

    return {}
