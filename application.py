import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
import bcrypt
import requests
import database_api_configs

app = Flask(__name__)
api_key = database_api_configs.apikey
os.environ["DATABASE_URL"] = database_api_configs.database_url

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['JSON_SORT_KEYS'] = False
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session.clear()
        if request.form.get("password") == request.form.get("confirmpassword"):
            password_hash = bcrypt.hashpw(request.form.get("password").encode("utf8"), bcrypt.gensalt())
            password_hash = password_hash.decode('utf8')
            db.execute(text("INSERT INTO users (username, password_hash) VALUES (:username, :passwordhash)"),
                        {"username":request.form.get("username"), "passwordhash":password_hash})
            db.commit()

            user = db.execute(text("SELECT * FROM users WHERE username = :username"),
                          {"username":request.form.get("username")}).fetchall()

            if len(user) == 1:
                session["user_id"] = user[0]["user_id"]
                return redirect("/")
            else:
                return render_template("error.html", error_message="Couldn't registered")
        else:
            return render_template("error.html", error_message="Passwords doesn't match")
    else:
        return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password_entered = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username=:username", {"username":username}).fetchall()
        if bcrypt.checkpw(password_entered.encode('utf8'), user[0]["password_hash"].encode('utf8')):
            session["user_id"] = user[0]["user_id"]
            return redirect("/")
        else:
            return render_template("error.html", error_message = "Couldn't find an user that match your credentials.")
    else:
        return render_template("login.html")

@app.route("/search")
def search():
    search = request.args.get("search")
    searchby = request.args.get("searchby")
    if searchby == "title":
        results = db.execute(text("SELECT * FROM books WHERE LOWER(title) LIKE :search"), {"search":"%" + search.lower() + "%"}).fetchall()
    if searchby == "isbn":
        results = db.execute(text("SELECT * FROM books WHERE isbn LIKE :search"), {"search":"%" + search + "%"}).fetchall()
    if searchby == "author":
        results = db.execute(text("SELECT * FROM books WHERE LOWER(author) LIKE :search"), {"search":"%" + search.lower() + "%"}).fetchall()
    if len(results) == 0:
        return render_template("error.html", error_message="Couldn't find a book that matches your search") 
    else:
        return render_template("search.html", results=results)

@app.route("/book/<isbn>", methods=['GET', 'POST'])
def book(isbn):
    if request.method == "POST":
        if session.get("user_id"):
            review_text = request.form.get("review_text")
            review_score = request.form.get("review_score")
            reviewes_of_user = db.execute(text("SELECT * FROM reviews WHERE reviewed_book_isbn = :isbn AND reviewer_id = :user_id"), {"isbn":isbn, "user_id": session["user_id"]}).fetchall()
            if len(reviewes_of_user) == 0:
                db.execute(text("INSERT INTO reviews (reviewer_id, reviewed_book_isbn, review_text, review_score) VALUES (:user_id, :book_isbn, :review_text, :review_score)"), {"user_id":session["user_id"], "book_isbn":isbn, "review_text":review_text, "review_score":review_score})
                db.commit()
                return redirect(url_for("book", isbn=isbn))
            else:
                return render_template("error.html", error_message="You have already submitted a review to this book.")
        else:
            return redirect(url_for("login"))
    else:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": api_key, "isbns":isbn}).json()
        api_averagerating = res["books"][0]["average_rating"]
        api_numofratings = res["books"][0]["work_reviews_count"]
        book = db.execute(text("SELECT * FROM books WHERE books.isbn = :isbn"), {"isbn":isbn}).fetchone()
        reviews = db.execute(text("SELECT reviews.review_time, reviews.review_text, reviews.review_score, users.username FROM reviews FULL JOIN users ON users.user_id = reviews.reviewer_id WHERE reviewed_book_isbn = :isbn ORDER BY reviews.review_time DESC"), {"isbn":isbn}).fetchall()
        return render_template("book.html", book=book, reviews=reviews, api_averagerating=api_averagerating, api_numofratings=api_numofratings)

@app.route("/api/<isbn>")
def api(isbn):
    book = db.execute(text("SELECT title, author, year FROM books WHERE isbn = :isbn"), {"isbn":isbn}).fetchone()
    if len(book) != 0:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": api_key, "isbns":isbn})
        json_book = dict()
        json_book["title"] = book.title
        json_book["author"] = book.author
        json_book["year"] = book.year
        json_book["isbn"] = isbn
        json_book["review_count"] = res.json()["books"][0]["reviews_count"]
        json_book["average_score"] = res.json()["books"][0]["average_rating"]
        return jsonify(json_book)
    else:
        return render_template("error.html", error_message="404 - Couldn't find a book with that ISBN"), 404

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")