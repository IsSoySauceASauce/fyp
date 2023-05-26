from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import abort
from flask import jsonify
from flask import session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import instaloader
import sams

app = Flask(__name__)
app.secret_key = "446ebb4ee6d962bbd5e7416bf4e7649f"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sams_db.db'
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
    date_created = db.Column(db.DateTime(), nullable=False, default=datetime.now())

@app.route('/app')
def home_page():
    return render_template('home.html')

@app.route('/app/analyze')
def analyze():
    return render_template('analyze.html')

@app.route('/app/predict')
def predict():
    return render_template('predict.html')

@app.route('/app/check_page_name', methods=['POST'])
def check_page_name():
    if request.method == 'POST':
        if "scraper" not in session:
            bot = instaloader.Instaloader(max_connection_attempts=3)
        else:
            bot = session['scraper']

        if not bot.context.is_logged_in:
            username = "refict689"
            password = "fict_insta689"

            try:
                bot.login(username, password)
            except:
                return jsonify({'error': 'Oops! There was a problem connecting to Instagram.'})
            
            session['scraper'] = bot
            
        page_name = request.form.get('page_name')
        try:
            profile = instaloader.Profile.from_username(bot.context, page_name)
        except:
            return jsonify({'error': 'The Instagram page was not found. Please enter a valid Instagram page name.'})

    return ('', 204)

@app.route('/app/scrape_classify', methods=['POST'])
def scrape_classify():
    if request.method == 'POST':
        return ('', 204)

@app.route('/app/sams_predict', methods=['POST'])
def sams_predict():
    if request.method == 'POST':
        text = request.form.get('post_text')
        sentiment = sams.predict('models/MLPClassifier.pickle', text)

        return jsonify({'sentiment': sentiment})

    return ('', 204)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home_page'))

@app.errorhandler(500)
def internal_server_error(e):
    return ('An internal server error has occured', 204)