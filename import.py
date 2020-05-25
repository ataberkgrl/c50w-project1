from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import os

engine = create_engine("postgres://ybzcrpuaoapnha:9e33420befd8bc3c771cb0a6913d470ce26ffca1d66dfae68dce5ba5b7f972dc@ec2-54-195-247-108.eu-west-1.compute.amazonaws.com:5432/d9pcstm2bohlos")

with engine.connect() as connection:
    connection.execute("CREATE TABLE IF NOT EXISTS books (isbn TEXT NOT NULL, title TEXT NOT NULL, author TEXT NOT NULL, year TEXT NOT NULL)")
    with open('books.csv') as csvfile:
        books = csv.DictReader(csvfile, delimiter=',')
        for book in books:
            connection.execute(text("INSERT INTO books(isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"), isbn=book["isbn"], title=book["title"], author=book["author"], year=book["year"])



