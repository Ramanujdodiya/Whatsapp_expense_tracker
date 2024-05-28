import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

config = {
    'user': os.getenv("DDBB_USER"),
    'password': os.getenv("DDBB_PASSWORD"),
    'host': os.getenv("DDBB_HOST"),
    'database': os.getenv("DDBB_DATABASE"),
    'port': os.getenv("DDBB_PORT"),
}

try:
    connection = mysql.connector.connect(**config)
    if connection.is_connected():
        print("Connected to MySQL database")
    connection.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")
