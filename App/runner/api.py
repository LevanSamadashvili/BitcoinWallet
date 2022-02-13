import sqlite3
from sqlite3 import Connection
from typing import Optional

from fastapi import Depends, FastAPI, Header, Response

from App.core.bitcoin_core import BitcoinCore
from App.core.constants import HTTP_DICT
from App.core.core_requests import (
    CreateWalletRequest,
    GetBalanceRequest,
    GetStatisticsRequest,
    GetTransactionsRequest,
    GetWalletTransactionsRequest,
    MakeTransactionRequest,
    RegisterUserRequest,
)
from App.core.core_responses import ResponseContent
from App.infra.btc_usd import default_btc_usd_convertor
from App.infra.repositories.statistics_repository import SQLiteStatisticsRepository
from App.infra.repositories.transactions_repository import SQLiteTransactionsRepository
from App.infra.repositories.user_repository import SQLiteUserRepository
from App.infra.repositories.wallet_repository import SQLiteWalletRepository
from App.infra.strategies import (
    default_transaction_fee,
    random_address_generator,
    random_api_key_generator,
)

app = FastAPI()


class GetConnection:
    connection = None

    def get_connection(self) -> Connection:
        if self.connection is None:
            self.connection = sqlite3.connect(
                "App/infra/database.db", check_same_thread=False
            )
        return self.connection


get_connection = GetConnection()


def get_core() -> BitcoinCore:
    connection = get_connection.get_connection()
    return BitcoinCore(
        user_repository=SQLiteUserRepository(connection=connection),
        wallet_repository=SQLiteWalletRepository(connection=connection),
        transactions_repository=SQLiteTransactionsRepository(connection=connection),
        statistics_repository=SQLiteStatisticsRepository(connection=connection),
        api_key_generator_strategy=random_api_key_generator,
        address_generator_strategy=random_address_generator,
        btc_usd_convertor_strategy=default_btc_usd_convertor,
        transaction_fee_strategy=default_transaction_fee,
    )


@app.post(
    "/users",
    responses={
        201: {"description": "User created successfully"},
        500: {"description": "User registration error"},
    },
)
def register_user(
    response: Response,
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> ResponseContent:
    """
    - Registers user
    - Returns API key that can authenticate all subsequent requests for this user
    """

    register_user_response = bitcoin_core.register_user(RegisterUserRequest())
    response.status_code = HTTP_DICT[register_user_response.status_code]
    return register_user_response.response_content


@app.post(
    "/wallets",
    responses={
        201: {"description": "Wallet created successfully"},
        400: {"description": "Bad request"},
        403: {"description": "Can't create more wallets"},
        404: {"description": "Invalid API key"},
        500: {"description": "Wallet creation error"},
    },
)
def create_wallet(
    response: Response,
    api_key: Optional[str] = Header(None),
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> ResponseContent:
    """
     - Requires API key
     - Create BTC wallet
     - Deposits 1 BTC (or 100000000 satoshis) automatically to the new
    wallet
     - User may register up to 3 wallets
     - Returns wallet address and balance in BTC and USD
    """

    if api_key is None:
        response.status_code = 400
        return ResponseContent()

    create_wallet_response = bitcoin_core.create_wallet(
        CreateWalletRequest(api_key=api_key)
    )
    response.status_code = HTTP_DICT[create_wallet_response.status_code]
    return create_wallet_response.response_content


@app.get(
    "/wallets/{address}",
    responses={
        200: {"description": "Got balance successfully"},
        400: {"description": "Bad request"},
        403: {"description": "Wallet doesn't exist"},
        404: {"description": "Invalid API key"},
    },
)
def get_balance(
    response: Response,
    address: Optional[str] = Header(None),
    api_key: Optional[str] = Header(None),
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> ResponseContent:
    """
    - Requires API key
    - Returns wallet address and balance in BTC and USD
    """
    if address is None or api_key is None:
        response.status_code = 400
        return ResponseContent()

    get_balance_response = bitcoin_core.get_balance(
        GetBalanceRequest(api_key=api_key, address=address)
    )
    response.status_code = HTTP_DICT[get_balance_response.status_code]
    return get_balance_response.response_content


@app.post(
    "/transactions",
    responses={
        200: {"description": "Successful transaction"},
        400: {"description": "Bad request"},
        403: {"description": "Wallet doesn't exist"},
        404: {"description": "Invalid API key"},
        452: {"description": "Not enough money on the wallet"},
        500: {"description": "Couldn't make transaction"},
    },
)
def make_transaction(
    response: Response,
    api_key: Optional[str] = Header(None),
    first_wallet_address: Optional[str] = Header(None),
    second_wallet_address: Optional[str] = Header(None),
    btc_amount: Optional[float] = Header(None),
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> ResponseContent:
    """
    - Requires API key
    - Makes a transaction from one wallet to another
    - Transaction is free if the same user is the owner of both wallets
    - System takes a 1.5% (of the transferred amount) fee for transfers
    to the foreign wallets
    """

    if (
        api_key is None
        or first_wallet_address is None
        or second_wallet_address is None
        or btc_amount is None
    ):
        response.status_code = 400
        return ResponseContent()

    make_transaction_response = bitcoin_core.make_transaction(
        MakeTransactionRequest(
            api_key=api_key,
            first_wallet_address=first_wallet_address,
            second_wallet_address=second_wallet_address,
            btc_amount=btc_amount,
        )
    )
    response.status_code = HTTP_DICT[make_transaction_response.status_code]
    return make_transaction_response.response_content


@app.get(
    "/transactions",
    responses={
        200: {"description": "Fetched transactions successfully"},
        400: {"description": "Bad request"},
        404: {"description": "Invalid API key"},
        500: {"description": "Couldn't fetch transactions"},
    },
)
def get_transactions(
    response: Response,
    api_key: Optional[str] = Header(None),
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> ResponseContent:
    """
    - Requires API key
    - Returns list of transactions
    """

    if api_key is None:
        response.status_code = 400
        return ResponseContent()

    get_transactions_response = bitcoin_core.get_transactions(
        GetTransactionsRequest(api_key=api_key)
    )
    response.status_code = HTTP_DICT[get_transactions_response.status_code]
    return get_transactions_response.response_content


@app.get(
    "/wallets/{address}/transactions",
    responses={
        200: {"description": "Fetched transactions successfully"},
        400: {"description": "Bad request"},
        403: {"description": "Wallet doesn't exist"},
        404: {"description": "Invalid API key"},
        500: {"description": "Couldn't fetch transactions"},
    },
)
def get_wallet_transactions(
    response: Response,
    api_key: Optional[str] = Header(None),
    address: Optional[str] = Header(None),
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> ResponseContent:
    """
    - Requires API key
    - returns transactions related to the wallet
    """

    if api_key is None or address is None:
        response.status_code = 400
        return ResponseContent()

    get_wallet_transactions_response = bitcoin_core.get_wallet_transactions(
        GetWalletTransactionsRequest(api_key=api_key, address=address)
    )

    response.status_code = HTTP_DICT[get_wallet_transactions_response.status_code]
    return get_wallet_transactions_response.response_content


@app.get(
    "/statistics",
    responses={
        200: {"description": "Fetched statistics successfully"},
        400: {"description": "Bad request"},
        404: {"description": "Invalid API key"},
        500: {"description": "Couldn't fetch statistics"},
    },
)
def get_statistics(
    response: Response,
    admin_api_key: Optional[str] = Header(None),
    bitcoin_core: BitcoinCore = Depends(get_core),
) -> ResponseContent:
    """
    - Requires pre-set (hard coded) Admin API key
    - Returns the total number of transactions and platform profit
    """

    if admin_api_key is None:
        response.status_code = 400
        return ResponseContent()

    get_statistics_response = bitcoin_core.get_statistics(
        GetStatisticsRequest(api_key=admin_api_key)
    )
    response.status_code = HTTP_DICT[get_statistics_response.status_code]
    return get_statistics_response.response_content
