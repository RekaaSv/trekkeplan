import configparser

import mysql.connector


class ConnectionManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.log = True

    def get_connection(self):
        try:
            if self.log: print("get_connection")
            host = self.db_config.get("host", "localhost")
            port = self.db_config.getint("port", 3306)
            user = self.db_config["user"]
            password = self.db_config["password"]
            database = self.db_config["database"]

            if self.log: print(f"Kobler til: {host}:{port} bruker={user} db={database}")

            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            if self.log: print("Connection established")
            return conn
        except Exception as e:
            print("❌ Feil ved tilkobling:", e)
            return None
