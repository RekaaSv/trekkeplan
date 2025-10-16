import configparser
import mysql.connector

def get_connection():
#    print("get_connection start")
    try:
        db_config = hent_mysql_config()
        connection = mysql.connector.connect(**db_config)
#        print("get_connection slutt")
        return connection
    except Exception as e:
        print("Feil: {e}")


def hent_mysql_config(filnavn="trekkeplan.cfg"):
    config = configparser.ConfigParser()
    config.read(filnavn)

    if "mysql" not in config:
        raise ValueError("Mangler [mysql]-seksjon i config-filen")

    return {
        "host": config["mysql"].get("host", "localhost"),
        "port": config["mysql"].getint("port", 3306),
        "user": config["mysql"]["user"],
        "password": config["mysql"]["password"],
        "database": config["mysql"]["database"],
    }