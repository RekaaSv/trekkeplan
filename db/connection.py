import configparser

import mysql.connector


class ConnectionManager:
    def __init__(self, config):
        self.config = config
        self.log = True

    @staticmethod
    def validate_config(filnavn="trekkeplan.cfg"):
        config = configparser.ConfigParser()
        config.read(filnavn)

        if "mysql" not in config:
            print("❌ Mangler [mysql]-seksjon i config")
            return

        db = config["mysql"]
        required_keys = ["host", "port", "user", "password", "database"]
        for key in required_keys:
            if key not in db:
                print(f"❌ Mangler nøkkel: {key}")
                return

        print("✅ Config ser OK ut")
        conn_mgr = ConnectionManager(config)
        conn = conn_mgr.get_connection()
        if conn:
            print("✅ Databaseforbindelse etablert")
            return conn_mgr
        else:
            print("❌ Klarte ikke å koble til databasen")
            return None

    def get_connection(self):
        try:
            if self.log: print("get_connection")
            db = self.config["mysql"]

            host = db.get("host", "localhost")
            port = db.getint("port", 3306)
            user = db["user"]
            password = db["password"]
            database = db["database"]

            print(f"Kobler til: {host}:{port} bruker={user} db={database}")

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
