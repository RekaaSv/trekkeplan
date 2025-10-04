import mysql.connector
from config import DB_HOST, DB_USER, DB_PASS, DB_NAME

def get_connection():
#    print("get_connection start")
    try:
        connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
        )
#        print("get_connection slutt")
        return connection
    except Exception as e:
        print("Feil: {e}")