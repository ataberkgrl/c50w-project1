from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import os
import database_api_configs

engine = create_engine(database_api_configs.database_url)

with engine.connect() as connection:
    connection.execute("CREATE TABLE IF NOT EXISTS books (isbn TEXT NOT NULL, title TEXT NOT NULL, author TEXT NOT NULL, year TEXT NOT NULL)")
    with open('books.csv') as csvfile:
        books = csv.DictReader(csvfile, delimiter=',')
        for book in books:
            connection.execute(text("INSERT INTO books(isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"), isbn=book["isbn"], title=book["title"], author=book["author"], year=book["year"])



