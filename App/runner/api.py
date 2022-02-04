from fastapi import Depends, FastAPI, Response

from App.core import status
from App.core.bitcoin_core import BitcoinCore
from App.core.requests import (
    CreateWalletRequest,
    GetBalanceRequest,
    GetStatisticsRequest,
    GetTransactionsRequest,
    GetWalletTransactionsRequest,
    MakeTransactionRequest,
    RegisterUserRequest,
)
from App.core.responses import (
    CreateWalletResponse,
    GetBalanceResponse,
    GetStatisticsResponse,
    GetTransactionsResponse,
    GetWalletTransactionsResponse,
    MakeTransactionResponse,
    RegisterUserResponse,
)

app = FastAPI()


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


@app.post(
    "/wallets",
    responses={status.NO_API_KEY: {"description": "API Key is not provided"}},
)
def create_wallet(
    response: Response,
    api_key: str,
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

    create_wallet_response = bitcoin_core.create_wallet(
        CreateWalletRequest(api_key=api_key)
    )
    response.status_code = create_wallet_response.status_code
    return create_wallet_response


@app.get("/wallets/{address}")
def get_balance(
    response: Response,
    address: str,
    api_key: str,
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> GetBalanceResponse:
    """
    - Requires API key
    - Returns wallet address and balance in BTC and USD
    """

    get_balance_response = bitcoin_core.get_balance(
        GetBalanceRequest(api_key=api_key, address=address)
    )
    response.status_code = get_balance_response.status_code
    return get_balance_response


@app.post("/transactions")
def make_transaction(
    response: Response,
    api_key: str,
    first_wallet_address: str,
    second_wallet_address: str,
    btc_amount: float,
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> MakeTransactionResponse:
    """
    - Requires API key
    - Makes a transaction from one wallet to another
    - Transaction is free if the same user is the owner of both wallets
    - System takes a 1.5% (of the transferred amount) fee for transfers
    to the foreign wallets
    """

    make_transaction_response = bitcoin_core.make_transaction(
        MakeTransactionRequest(
            api_key=api_key,
            first_wallet_address=first_wallet_address,
            second_wallet_address=second_wallet_address,
            btc_amount=btc_amount,
        )
    )
    response.status_code = make_transaction_response.status_code
    return make_transaction_response


@app.get("/transactions")
def get_transactions(
    response: Response, api_key: str, bitcoin_core: BitcoinCore = Depends(get_core)
) -> GetTransactionsResponse:
    """
    - Requires API key
    - Returns list of transactions
    """

    get_transactions_response = bitcoin_core.get_transactions(
        GetTransactionsRequest(api_key=api_key)
    )
    response.status_code = get_transactions_response.status_code
    return get_transactions_response


@app.get("/wallets/{address}/transactions")
def get_wallet_transactions(
    response: Response,
    api_key: str,
    address: str,
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> GetWalletTransactionsResponse:
    """
    - Requires API key
    - returns transactions related to the wallet
    """

    get_wallet_transactions_response = bitcoin_core.get_wallet_transactions(
        GetWalletTransactionsRequest(api_key=api_key, address=address)
    )

    response.status_code = get_wallet_transactions_response.status_code
    return get_wallet_transactions_response


@app.get("/statistics")
def get_statistics(
    response: Response,
    admin_api_key: str,
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> GetStatisticsResponse:
    """
    - Requires pre-set (hard coded) Admin API key
    - Returns the total number of transactions and platform profit
    """

    get_statistics_response = bitcoin_core.get_statistics(
        GetStatisticsRequest(api_key=admin_api_key)
    )
    response.status_code = get_statistics_response.status_code
    return get_statistics_response
