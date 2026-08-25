import sqlite3

DB_PATH = "roomloop.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()

    with open("schema.sql", "r") as file:
        schema = file.read()

    connection.executescript(schema)
    connection.close()