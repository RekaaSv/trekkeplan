import logging

import pymysql


class ConnectionManager:
    def __init__(self, db_config):
        self.db_config = db_config

    def get_connection(self):
        try:
            logging.debug("get_connection")
            host = self.db_config.get("host", "localhost")
            port = self.db_config.getint("port", 3306)
            user = self.db_config["user"]
            password = self.db_config["password"]
            database = self.db_config["database"]

            logging.debug(f"Kobler til: {host}:{port} bruker={user} db={database}")

            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            logging.debug("Connection established")
            return conn
        except Exception as e:
            logging.error("❌ Feil ved tilkobling: %s", e)
            raise
