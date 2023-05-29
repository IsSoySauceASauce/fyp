from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import abort
from flask import jsonify
from flask import session
from sqlalchemy import desc
from flask_sqlalchemy import SQLAlchemy
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from datetime import datetime
from datetime import timedelta
import instaloader
import nltk
import sqlite3
import io
import base64
import pandas
import numpy
import string
import re
import sams

sqlite3.register_adapter(numpy.int64, lambda val: int(val))

app = Flask(__name__)
app.secret_key = "446ebb4ee6d962bbd5e7416bf4e7649f"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sams_db.db'
db = SQLAlchemy(app)

all_comments = []
malay_stopwords = numpy.load('data/malay_stopwords.npy')

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

class PageSentimentVisualisation:
    def __init__(self, id, page_name, sentiment_graph, positive_words_graph, negative_words_graph, date_created):
        self.id=id
        self.page_name=page_name
        self.sentiment_graph=sentiment_graph
        self.positive_words_graph=positive_words_graph
        self.negative_words_graph=negative_words_graph
        self.date_created=date_created

def skip_unwanted(pos_tuple):
    unwanted = nltk.corpus.stopwords.words("english")
    unwanted.extend(malay_stopwords)

    word, tag = pos_tuple
    if not word.isalpha() or word in unwanted:
        return False
    if word in string.punctuation:
        return False
    return True

@app.route('/app')
def home_page():
    return render_template('home.html')

@app.route('/app/analyze')
def analyze():
    return render_template('analyze.html')

@app.route('/app/history')
def history():
    page_sentiments = PageSentiment.query.order_by(desc(PageSentiment.date_created)).all()

    page_sentiment_visualisations = []
    for page_sentiment in page_sentiments:
        fig = Figure(figsize=[5, 4])

        labels = ['positive', 'negative']
        sizes = [page_sentiment.positive_sentiment_count, page_sentiment.negative_sentiment_count]
        colors = ['#55B9F3', '#F08080']
        wedgeprops = {'width': 0.2, 'edgecolor': 'w'}
        textprops = {'fontsize': 11, 'fontname': 'Montserrat'}

        ax = fig.subplots()
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, radius=0.5, wedgeprops=wedgeprops, textprops=textprops, pctdistance=0.8)
        ax.axis('equal')
        ax.set_title(F"{page_sentiment.page_name}'s Page Sentiment", fontsize=11, fontdict={'fontname': 'Montserrat'})

        sentiment_graph_buffer = io.BytesIO()
        fig.savefig(sentiment_graph_buffer, format="png")
        sentiment_graph_output = base64.b64encode(sentiment_graph_buffer.getbuffer()).decode("ascii")

        positive_word_freqs = [int(item) for item in page_sentiment.positive_word_freqs.split(', ')]
        negative_word_freqs = [int(item) for item in page_sentiment.negative_word_freqs.split(', ')]

        positive_words = [item for item in page_sentiment.positive_words.split(', ')]
        negative_words = [item for item in page_sentiment.negative_words.split(', ')]

        positive_df = pandas.DataFrame([positive_words, positive_word_freqs]).T
        positive_df.columns = ['word', 'count']

        negative_df = pandas.DataFrame([negative_words, negative_word_freqs]).T
        negative_df.columns = ['word', 'count']

        colors = plt.cm.get_cmap('Set2', len(positive_df))
        colors = plt.cm.get_cmap('Set2', len(negative_df))

        fig2 = Figure(figsize=[4.75, 5])
        ax2 = fig2.subplots()
        ax2.bar(positive_df['word'], positive_df['count'], color=colors(range(len(positive_df))))
        ax2.set_xticklabels(positive_df['word'], rotation=90, fontsize=11, fontdict={'fontname': 'Montserrat'})
        ax2.set_xlabel('Words', fontsize=11, fontdict={'fontname': 'Montserrat'})
        ax2.set_ylabel('Frequency', fontsize=11, fontdict={'fontname': 'Montserrat'})
        ax2.set_title('Top 20 Words in Positive Comments', fontsize=11, fontdict={'fontname': 'Montserrat'})
        for spine in ax2.spines.values():
            spine.set_visible(False)
        ax2.tick_params(bottom=False, left=False)

        positive_words_graph_buffer = io.BytesIO()
        fig2.savefig(positive_words_graph_buffer, format="png")
        positive_words_graph_output = base64.b64encode(positive_words_graph_buffer.getbuffer()).decode("ascii")

        fig3 = Figure(figsize=[4.75, 5])
        ax3 = fig3.subplots()
        ax3.bar(negative_df['word'], negative_df['count'], color=colors(range(len(negative_df))))
        ax3.set_xticklabels(negative_df['word'], rotation=90, fontsize=11, fontdict={'fontname': 'Montserrat'})
        ax3.set_xlabel('Words', fontsize=11, fontdict={'fontname': 'Montserrat'})
        ax3.set_ylabel('Frequency', fontsize=11, fontdict={'fontname': 'Montserrat'})
        ax3.set_title('Top 20 Words in Negative Comments', fontsize=11, fontdict={'fontname': 'Montserrat'})
        for spine in ax3.spines.values():
            spine.set_visible(False)
        ax.tick_params(bottom=False, left=False)

        negative_words_graph_buffer = io.BytesIO()
        fig3.savefig(negative_words_graph_buffer, format="png")
        negative_words_graph_output = base64.b64encode(negative_words_graph_buffer.getbuffer()).decode("ascii")

        id = page_sentiment.id
        page_name = page_sentiment.page_name
        date_created = page_sentiment.date_created

        page_sentiment_visualisations.append(PageSentimentVisualisation(
            id=id, 
            page_name=page_name, 
            sentiment_graph=sentiment_graph_output,
            positive_words_graph=positive_words_graph_output,
            negative_words_graph=negative_words_graph_output,
            date_created=date_created
        ))

    return render_template('history.html', page_sentiment_visualisations=page_sentiment_visualisations)

@app.route('/app/predict')
def predict():
    return render_template('predict.html')

@app.route('/app/check_page_name', methods=['POST'])
def check_page_name():
    if request.method == 'POST':
        bot = instaloader.Instaloader(max_connection_attempts=1)

        if not bot.context.is_logged_in:
            try:
                bot.load_session_from_file('hazimridza')
            except:
                return jsonify({'error': 'There was a problem connecting to Instagram.'})
        
        if bot.test_login() is None:
            return jsonify({'error': 'There was a problem connecting to Instagram.'}) 
            
        page_name = request.form.get('page_name')
        try:
            profile = instaloader.Profile.from_username(bot.context, page_name)
            print('Page found.')
        except Exception as e:
            print(e)
            return jsonify({'error': 'The Instagram page was not found. Please enter a valid Instagram page name.'})

        session['page_name'] = page_name
        return jsonify({'success': True})

    return ('', 204)

@app.route('/app/scrape_classify', methods=['POST'])
def scrape_classify():
    if request.method == 'POST':
        bot = instaloader.Instaloader(max_connection_attempts=1)

        if not bot.context.is_logged_in:
            try:
                bot.load_session_from_file('hazimridza')
            except:
                return jsonify({'error': 'There was a problem connecting to Instagram.'})

        if bot.test_login() is None:
            return jsonify({'error': 'There was a problem connecting to Instagram.'})
            
        page_name = session['page_name']
        try:
            profile = instaloader.Profile.from_username(bot.context, page_name)
            print('Page found.')
        except Exception as e:
            print(e)
            return jsonify({'error': 'The Instagram page was not found. Please enter a valid Instagram page name.'})

        posts = profile.get_posts()

        TODAY = datetime.now()
        UNTIL = datetime.now() - timedelta(days = 30)

        all_comments.clear()
        try:
            print('Starting comments scraping.')
            post_count = 0
            for post in posts:
                post_count += 1

                if post_count <= 10:
                    postdate = post.date
                    if postdate > UNTIL and postdate <= TODAY:
                        comments = post.get_comments()
                        for comment in comments:
                            all_comments.append(comment.text)

                        if len(all_comments) >= 300:
                            print(F"\nObtained {len(all_comments)} comments.")
                            break

                        print(F"\nObtained {len(all_comments)} comments.")
                    else:
                        print(F"\nObtained {len(all_comments)} comments.")
                        break
                else:
                    print(F"\nStopped at 10th post.")
                    break
        except Exception as e:
            print(e)
            return jsonify({'error': 'An HTTP 429 error was encountered. Please wait a few hours before continuing again.'})

    return jsonify({'success': True})

@app.route('/app/classify_store', methods=['POST'])
def classify_store():
    if request.method == 'POST':
        comment_texts = []
        sentiments = []
        for comment in all_comments:
            if any(c.isalpha() for c in comment):
                sentiment = sams.predict(comment)
                comment_texts.append(comment)
                sentiments.append(sentiment)

        sentiment_df = pandas.DataFrame([comment_texts, sentiments]).T
        sentiment_df.columns = ['comment', 'sentiment']

        if 'positive' in sentiment_df['sentiment'].values:
            positive_count = sentiment_df.sentiment[sentiment_df['sentiment'] == 'positive'].count()
        else:
            positive_count = 0
        
        if 'negative' in sentiment_df['sentiment'].values:
            negative_count = sentiment_df.sentiment[sentiment_df['sentiment'] == 'negative'].count()
        else:
            negative_count = 0

        print(positive_count)
        print(negative_count)

        comments_df = sentiment_df['comment']
        positive_comments = numpy.array(comments_df[sentiment_df['sentiment'] == 'positive'])
        negative_comments = numpy.array(comments_df[sentiment_df['sentiment'] == 'negative'])

        positive_words = []
        for positive_comment in positive_comments :
            positive_comment = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+','', positive_comment)
            positive_comment = re.sub('(@[A-Za-z0-9_]+)','', positive_comment)

            positive_comment = positive_comment.lower()
            positive_words.extend(nltk.pos_tag(nltk.word_tokenize(positive_comment)))

        positive_words = [word for word, tag in filter(
            skip_unwanted,
            positive_words)
        ]

        negative_words = []
        for negative_comment in negative_comments :
            negative_comment = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+','', negative_comment)
            negative_comment = re.sub('(@[A-Za-z0-9_]+)','', negative_comment)

            negative_comment = negative_comment.lower()
            negative_words.extend(nltk.pos_tag(nltk.word_tokenize(negative_comment)))

        negative_words = [word for word, tag in filter(
            skip_unwanted,
            negative_words)
        ]

        positive_fd = nltk.FreqDist(positive_words)
        negative_fd = nltk.FreqDist(negative_words)
        common_set = set(positive_fd).intersection(negative_fd)

        for word in common_set:
            del positive_fd[word]
            del negative_fd[word]
            
        positive_word_top_20 = [[word, count] for word, count in positive_fd.most_common(20)]
        negative_word_top_20 = [[word, count] for word, count in negative_fd.most_common(20)]

        positive_df = pandas.DataFrame(positive_word_top_20)
        positive_df.columns = ['word', 'count']

        negative_df = pandas.DataFrame(negative_word_top_20)
        negative_df.columns = ['word', 'count']

        positive_words_20_string = ', '.join(positive_df['word'].tolist())
        negative_words_20_string = ', '.join(negative_df['word'].tolist())

        positive_words_20_freqs = ', '.join(str(i) for i in positive_df['count'].tolist())
        negative_words_20_freqs = ', '.join(str(i) for i in negative_df['count'].tolist())

        new_page_sentiment = PageSentiment(
            page_name = session['page_name'],
            positive_sentiment_count = positive_count,
            negative_sentiment_count = negative_count,
            positive_words = positive_words_20_string,
            positive_word_freqs = positive_words_20_freqs,
            negative_words = negative_words_20_string,
            negative_word_freqs = negative_words_20_freqs
        )

        try:
            print('Adding data to database.')
            db.session.add(new_page_sentiment)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            print(e)
            return jsonify({'error': 'Error while storing sentiment analysis results to database.'})

@app.route('/app/sams_predict', methods=['POST'])
def sams_predict():
    if request.method == 'POST':
        text = request.form.get('post_text')
        sentiment = sams.predict(text, 'models/MLPClassifier.pickle')

        return jsonify({'sentiment': sentiment})

    return ('', 204)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home_page'))

@app.errorhandler(500)
def internal_server_error(e):
    return ('An internal server error has occured', 204)