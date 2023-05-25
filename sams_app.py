from flask import Flask
from flask import render_template
from flask import url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sams.db'
db = SQLAlchemy(app)

class PageSentiment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    page_name = db.Column(db.String(length=30), nullable=False, unique=True)
    positive_sentiment_count = db.Column(db.Integer(), nullable=False)
    negative_sentiment_count = db.Column(db.Integer(), nullable=False)
    positive_words = db.Column(db.String(length=512), nullable=False)
    positive_word_freqs = db.Column(db.String(length=128), nullable=False)
    negative_words = db.Column(db.String(length=512), nullable=False)
    negative_word_freqs = db.Column(db.String(length=128), nullable=False)

@app.route('/app')
def home_page():
    return render_template('home.html')