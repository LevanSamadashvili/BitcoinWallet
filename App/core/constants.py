from App.core import status

ADMIN_API_KEY = "3.14"
MAX_AVAILABLE_WALLETS = 3
INITIAL_BITCOINS_WALLET = 1.0
ADDRESS_LENGTH = 8
API_KEY_LENGTH = 24

HTTP_DICT = {
    status.GOT_BALANCE_SUCCESSFULLY: 200,
    status.TRANSACTION_SUCCESSFUL: 200,
    status.FETCH_TRANSACTIONS_SUCCESSFUL: 200,
    status.FETCH_STATISTICS_SUCCESSFUL: 200,
    status.USER_CREATED_SUCCESSFULLY: 201,
    status.WALLET_CREATED_SUCCESSFULLY: 201,
    status.CANT_CREATE_MORE_WALLETS: 403,
    status.NOT_YOUR_WALLET: 403,
    status.INVALID_WALLET: 403,
    status.INCORRECT_API_KEY: 404,
    status.NOT_ENOUGH_BALANCE: 452,
    status.USER_REGISTRATION_ERROR: 500,
    status.WALLET_CREATION_ERROR: 500,
    status.TRANSACTION_UNSUCCESSFUL: 500,
    status.FETCH_TRANSACTIONS_UNSUCCESSFUL: 500,
    status.FETCH_STATISTICS_UNSUCCESSFUL: 500,
}
