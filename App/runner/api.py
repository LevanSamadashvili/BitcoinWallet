from fastapi import FastAPI

app = FastAPI()


@app.post("/users")
def register_user(body: dict[str, str]) -> dict[str, str]:
    """
    - Registers user
    - Returns API key that can authenticate all subsequent requests for this user
    """

    print(body["id"])

    return {"key": "asfa"}


@app.post("/wallets")
def create_wallet(body: dict[str, str]) -> dict[str, str]:
    """
     - Requires API key
     - Create BTC wallet
     - Deposits 1 BTC (or 100000000 satoshis) automatically to the new
    wallet
     - User may register up to 3 wallets
     - Returns wallet address and balance in BTC and USD
    """

    return {}


@app.get("/wallets/{address}")
def get_balance(body: dict[str, str], address: str) -> dict[str, str]:
    """
    - Requires API key
    - Returns wallet address and balance in BTC and USD
    """

    return {}


@app.post("/transactions")
def make_transaction(body: dict[str, str]) -> dict[str, str]:
    """
    - Requires API key
    - Makes a transaction from one wallet to another
    - Transaction is free if the same user is the owner of both wallets
    - System takes a 1.5% (of the transferred amount) fee for transfers
    to the foreign wallets
    """

    return {}


@app.get("/transactions")
def get_transactions(body: dict[str, str]) -> dict[str, str]:
    """
    - Requires API key
    - Returns list of transactions
    """

    return {}


@app.get("/wallets/{address}/transactions")
def get_wallet_transactions(body: dict[str, str], address: str) -> dict[str, str]:
    """
    - Requires API key
    - returns transactions related to the wallet
    """

    return {}


@app.get("/statistics")
def get_statistics(body: dict[str, str]) -> dict[str, str]:
    """
    - Requires pre-set (hard coded) Admin API key
    - Returns the total number of transactions and platform profit
    """

    return {}
