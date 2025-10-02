from db.connection import get_connection

try:
    conn = get_connection()
    print("Tilkobling OK")
    conn.close()
except Exception as e:
    print(f"Feil: {e}")
