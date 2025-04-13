import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from fastapi import Depends, HTTPException, status

load_dotenv()  # Load environment variables from .env

def get_db():
    user_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT')),
        'database': os.getenv('DB_NAME'),
        'ssl_ca': os.getenv('DB_SSL_CA'),
    }

    try:
        connection = mysql.connector.connect(**user_config)
        if connection.is_connected():
            cursor = connection.cursor()
            return {"status": "Connected to the database"}
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to the database: {str(e)}",
        )

def db_connect():
    user_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT')),
        'database': os.getenv('DB_NAME'),
        'ssl_ca': os.getenv('DB_SSL_CA'),
    }

    try:
        connection = mysql.connector.connect(**user_config)  
        return connection
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to the database: {str(e)}",
        )

def close_db_connection(cursor, connection):
    """Close the database connection."""
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
