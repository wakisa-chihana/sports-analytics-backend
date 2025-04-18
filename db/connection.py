import os
import psycopg2
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status

load_dotenv()  # Load environment variables from .env

def get_db():
    try:
        connection = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
        )
        cursor = connection.cursor()
        return {"status": "Connected to the PostgreSQL database"}
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PostgreSQL connection error: {str(e)}"
        )

def db_connect():
    try:
        connection = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
        )
        return connection
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PostgreSQL connection error: {str(e)}"
        )

def close_db_connection(cursor, connection):
    """Close the database connection."""
    if cursor:
        cursor.close()
    if connection:
        connection.close()
