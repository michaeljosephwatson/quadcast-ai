from psycopg2 import connect
from psycopg2.extensions import connection
import os
from dotenv import load_dotenv

load_dotenv()  # .env for local development, ignored in production


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""
    conn = connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DB_NAME"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD"),
        port=int(os.getenv("RDS_PORT")),
    )
    return conn


if __name__ == "__main__":
    # Test the connection
    conn = get_rds_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM podcast")
        result = cursor.fetchall()
        print(
            f"Connection Successful! Found {len(result)} results")
    conn.close()
