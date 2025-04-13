from db.connection import get_db
from fastapi import FastAPI, Depends, HTTPException, status

def checkdb_connection():
    return get_db()

