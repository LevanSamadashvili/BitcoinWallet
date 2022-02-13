import sqlite3
from sqlite3 import Connection, Cursor


def create_tables(cursor: Cursor, connection: Connection) -> None:
    cursor.execute("""DROP TABLE users""")
    cursor.execute("""DROP TABLE wallets""")
    cursor.execute("""DROP TABLE transactions""")
    cursor.execute("""DROP TABLE statistics""")

    cursor.execute(
        """CREATE TABLE users
                               (api_key text,
                                PRIMARY KEY (`api_key`))"""
    )
    cursor.execute(
        """CREATE TABLE wallets
                               (address text,
                                api_key text,
                                balance number,
                                PRIMARY KEY (address),
                                FOREIGN KEY (api_key) REFERENCES users(api_key))"""
    )
    cursor.execute(
        """CREATE TABLE transactions
                                (first_address text,
                                 second_address text,
                                 amount number,
                                 FOREIGN KEY (first_address) REFERENCES wallets(address),
                                 FOREIGN KEY (second_address) REFERENCES wallets(address))"""
    )
    cursor.execute(
        """CREATE TABLE statistics
                                (num_transactions number,
                                 profit number)"""
    )
    connection.commit()


def setup_statistics(cursor: Cursor, connection: Connection) -> None:
    cursor.execute("INSERT INTO statistics (num_transactions, profit) VALUES(0, 0);")
    connection.commit()


if __name__ == "__main__":
    connection = sqlite3.connect("database.db", check_same_thread=False)
    cursor = connection.cursor()
    create_tables(cursor, connection)
    setup_statistics(cursor, connection)
    for api_key in cursor.execute("SELECT * FROM users"):
        print(api_key)
    print("users")
    for (address, api_key, balance) in cursor.execute("SELECT * FROM wallets"):
        print(address)
        print(api_key)
        print(balance)
    print("wallets")
    for (first_address, second_address, amount) in cursor.execute(
        "SELECT * FROM transactions"
    ):
        print(first_address)
        print(second_address)
        print(amount)
    print("transactions")
    for (num_transactions, profit) in cursor.execute("SELECT * FROM statistics"):
        print(num_transactions)
        print(profit)
    print("statistics")

    connection.close()
