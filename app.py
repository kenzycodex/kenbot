from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
import json
import requests
import logging
from flask import Flask, request, jsonify
from datetime import datetime
from bs4 import BeautifulSoup
from googlesearch import search
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from flask_debugtoolbar import DebugToolbarExtension
import numpy as np
import mysql.connector
import base64
import hashlib
from PIL import Image
from io import BytesIO
from base64 import b64decode
import re

# Load SpaCy model and sentiment analyzer
nlp = spacy.load("en_core_web_sm")
analyzer = SentimentIntensityAnalyzer()

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'kenzy123'
toolbar = DebugToolbarExtension(app)

# Create a connection to the MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="KENBOT",  # Change to your MySQL username
    password="kenbot3579",  # Change to your MySQL password
    database="kenbot"  # Ensure the database is created initially
)

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Create a table for user login information if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS kendata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    gender VARCHAR(50) NOT NULL,
    profile_pic LONGBLOB
)
"""
cursor.execute(create_table_query)
conn.commit()

# Check the database connection status
print(f"Database connection status: {conn.is_connected()}")


context = {
    "last_query": None,
    "last_response": None
}

user_data = {}

# Load ML model and vectorizer if available
try:
    with open("model.json", "r") as model_file:
        model = json.load(model_file)
        vectorizer = TfidfVectorizer()
        vectorizer.fit(model["X"])
        clf = LogisticRegression()
        clf.coef_ = np.array(model["coef"])
        clf.intercept_ = np.array(model["intercept"])
except (FileNotFoundError, json.JSONDecodeError):
    vectorizer = TfidfVectorizer()
    clf = LogisticRegression()

def train_model(interactions):
    X = [interaction["query"] for interaction in interactions]
    y = [interaction["response"] for interaction in interactions]
    
    # Check if there are valid interactions
    if not X or not y:
        print("Warning: No valid interactions found to train the model.")
        return
    
    X_vec = vectorizer.fit_transform(X)
    clf.fit(X_vec, y)
    model = {
        "X": vectorizer.get_feature_names_out().tolist(),
        "coef": clf.coef_.tolist(),
        "intercept": clf.intercept_.tolist()
    }
    with open("model.json", "w") as model_file:
        json.dump(model, model_file)

def get_clean_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for unwanted in soup(["script", "style", "header", "footer", "nav", "form", "aside", "iframe", "noscript", "svg"]):
            unwanted.decompose()
        paragraphs = soup.find_all('p')
        text = " ".join(p.get_text() for p in paragraphs[:4])
        return text.strip()
    except requests.RequestException as e:
        log_error(f"Error processing URL {url}: {e}")
        return None

def log_error(message):
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now().isoformat()}: {message}\n")

def google_custom_search(query, api_key, cx):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.RequestException as e:
        log_error(f"Error fetching custom search results for '{query}': {e}")
        return []

def perform_search(query):
    google_api_key = "AIzaSyDXyPPeMHRDQY82REpXqxY_Iz11POmZvjE"
    google_cx = "90738cc91c337468f"

    try:
        search_results = google_custom_search(query, google_api_key, google_cx)
        result_texts = []
        clickable_links = []

        for result in search_results:
            if isinstance(result, dict):
                link = result.get("link")
                if link:
                    text = get_clean_text(link)
                    if text:
                        result_texts.append(text)
                        clickable_links.append(link)
            elif isinstance(result, str):
                text = get_clean_text(result)
                if text:
                    result_texts.append(text)

        if not result_texts:
            basic_search_results = list(search(query))
            # basic_search_results = list(search(query, num_results=5, stop=5, pause=2))
            for result in basic_search_results:
                text = get_clean_text(result)
                if text:
                    result_texts.append(text)

        if result_texts:
            response = " ".join(result_texts[:2]) # Limit to first 2 paragraphs
            response = response[:700] + '...'  # Limit response to 700 characters
            if clickable_links:
                response += "\n\nClick here for more information:<br>"
                response += "<br>".join(f"<a href='{link}' target='_blank'>{link}</a>" for link in clickable_links[:2])

        else:
            response = "Sorry, I couldn't find relevant information."

        return format_response(response)
    except requests.RequestException as e:
        log_error(f"Network error while performing search: {e}")
        return "I'm currently having trouble connecting to the internet. Please try again later."

def format_response(response):
    # Clean up the response for better readability
    response = re.sub(r'\s+', ' ', response) # Remove extra whitespace
    # response = re.sub(r'http[s]?://\S+', '', response)
    response = re.sub(r'\.\s+', '.\n', response)  # Ensure a single space after periods

    # Capitalize the first letter after each period
    def capitalize_after_period(match):
        return match.group(0).capitalize()

    response = re.sub(r'(?<=\.\s)(\w)', capitalize_after_period, response)

    # Capitalize the first letter of the entire response
    if response:
        response = response[0].upper() + response[1:]

    return response.strip()

def get_weather(city):
    api_key = "748bf0260d4165ccb4c0927fdf23baa0"
    try:
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        response = requests.get(base_url)
        response.raise_for_status()
        weather_data = response.json()
        if weather_data["cod"] != "404":
            main = weather_data["main"]
            weather_description = weather_data["weather"][0]["description"]
            temperature = main["temp"]
            return f"The weather in {city} is currently {weather_description} with a temperature of {temperature - 273.15:.2f}°C."
    except requests.RequestException as e:
        log_error(f"Error fetching weather data for {city}: {e}")
        return "Sorry, I couldn't retrieve the weather information."

def get_global_news():
    api_key = "6183c180818d4f6eaabceccbe036f367"
    try:
        base_url = f"https://newsapi.org/v2/top-headlines?country=&apiKey={api_key}"
        response = requests.get(base_url)
        response.raise_for_status()
        news_data = response.json()
        articles = news_data["articles"]
        news_summary = "Here are the top global news headlines:\n"
        for i, article in enumerate(articles[:5], start=1):
            news_summary += f"{i}. {article['title']}\n"
        return news_summary
    except requests.RequestException as e:
        log_error(f"Error fetching global news: {e}")
        return "Sorry, I couldn't retrieve the global news."

def handle_special_cases(query):
    if "latest match" in query.lower():
        return "I don't have real-time capabilities to fetch the latest match information. Please check a sports news website for the latest updates."
    elif "weather" in query.lower():
        match = re.search(r'in\s+(.*)$', query, re.IGNORECASE)
        if (match):
            city = match.group(1).strip()
            return get_weather(city)
        return "Please specify a city for weather information."
    elif "news" in query.lower():
        return get_global_news()
    elif "currency of nigeria" in query.lower():
        return "The currency of Nigeria is the Nigerian Naira (NGN)."
    return None

def construct_reply(response):
    if response and response[-1] not in ['.', '!', '?']:
        response += '.'
    return response.capitalize()

def analyze_query(query):
    doc = nlp(query)
    question_words = ["who", "what", "how", "when", "which", "whose"]
    list_words = ["list", "outline", "state", "enumerate", "name"]
    return any(token.lower_ in question_words for token in doc), any(token.lower_ in list_words for token in doc)

def save_interaction(user_query, response):
    interaction = {"query": user_query, "response": response, "timestamp": datetime.now().isoformat()}
    with open("interactions.json", "a") as file:
        file.write(json.dumps(interaction) + "\n")

def load_interactions():
    try:
        with open("interactions.json", "r") as file:
            interactions = [json.loads(line) for line in file]
            return interactions
    except FileNotFoundError:
        return []

def respond_to_greeting():
    return "Hello! How can I help you today?"

def respond_to_goodbye():
    return "Goodbye! Have a nice day. Hope to see you again!"

def analyze_sentiment(text):
    sentiment_score = analyzer.polarity_scores(text)
    compound_score = sentiment_score['compound']
    if compound_score >= 0.05:
        return "positive"
    elif compound_score <= -0.05:
        return "negative"
    else:
        return "neutral"

def personalize_response(user_query, sentiment):
    if sentiment == "positive":
        return f"It's great to hear that! {user_query}"
    elif sentiment == "negative":
        return f"I'm sorry to hear that. {user_query}"
    else:
        return user_query

def detect_personal_info(query):
    doc = nlp(query)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE"]:
            return True
    return False

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if debug_mode:
            super().log_message(format, *args)

    def do_GET(self):
        url_path = urlparse(self.path).path

        if url_path == '/getUserProfile':
            query_components = parse_qs(urlparse(self.path).query)
            email = query_components.get('email', [None])[0]

            if email is None:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Email parameter is missing'}).encode())
                return

            try:
                cursor.execute("SELECT username, profile_pic FROM kendata WHERE email = %s", (email,))
                result = cursor.fetchone()
                if not result:
                    response = {'error': 'User not found'}
                else:
                    username, profile_pic = result
                    profile_pic_base64 = base64.b64encode(profile_pic).decode('utf-8')
                    
                    # Decode the profile picture and detect format using Pillow
                    profile_pic_data = base64.b64decode(profile_pic_base64)
                    profile_pic_image = Image.open(BytesIO(profile_pic_data))
                    profile_pic_format = profile_pic_image.format.lower()

                    # Save the profile picture as a file
                    profile_pic_filename = f"{username}_profile_pic.{profile_pic_format}"
                    profile_pic_image.save(profile_pic_filename)
                    
                    response = {
                        'username': username,
                        'profilePicFilename': profile_pic_filename
                    }
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                print(f"Error fetching user profile: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Internal Server Error'}).encode())

        # Handling other file requests
        else:
            file_path = './' + url_path.lstrip('/')
            if os.path.exists(file_path) and os.path.isfile(file_path):  # Ensure file_path points to a file
                with open(file_path, 'rb') as file:
                    if file_path.endswith('.css'):
                        self.send_response(200)
                        self.send_header('Content-type', 'text/css')
                    elif file_path.endswith('.js'):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/javascript')
                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(file.read())
            else:
                self.send_error(404, 'File Not Found: %s' % self.path)


    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')


        if self.path == '/saveData':
            try:
                params = json.loads(post_data)
                username = params.get('username', '')
                email = params.get('email', '')
                password = params.get('password', '')
                gender = params.get('gender', '')
                profile_pic_data = params.get('profilePic', '')

                if not (username and email and password and gender and profile_pic_data):
                    raise ValueError("All fields are required")

                # Hash the password
                hashed_password = hashlib.sha256(password.encode()).hexdigest()

                # Decode the profile picture
                profile_pic = b64decode(profile_pic_data.split(',')[1])

                # Check if the email already exists
                cursor.execute("SELECT * FROM kendata WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Email already exists.'}).encode())
                    return

                cursor.execute(
                    "INSERT INTO kendata (username, email, password, gender, profile_pic) VALUES (%s, %s, %s, %s, %s)",
                    (username, email, hashed_password, gender, profile_pic)
                )
                conn.commit()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'Data sent successfully'}).encode())

            except ValueError as ve:
                print(f"Validation Error: {str(ve)}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(ve)}).encode())

            except Exception as e:
                print(f"Error: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Internal Server Error'}).encode())

        elif self.path == '/login':
            try:
                params = json.loads(post_data)
                email = params.get('email', '')
                password = params.get('password', '')

                if not (email and password):
                    raise ValueError("Email and password are required")

                hashed_password = hashlib.sha256(password.encode()).hexdigest()

                cursor.execute("SELECT * FROM kendata WHERE email = %s AND password = %s", (email, hashed_password))
                user = cursor.fetchone()

                if user:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Login successful'}).encode())
                else:
                    self.send_response(401)  # Unauthorized
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Invalid email or password'}).encode())

            except ValueError as ve:
                print(f"Validation Error: {str(ve)}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(ve)}).encode())

            except Exception as e:
                print(f"Error: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Internal Server Error'}).encode())

        elif self.path == '/chat':
            try:
                parsed_data = parse_qs(post_data)
                user_query = parsed_data.get('query', [''])[0]

                interactions = load_interactions()
                train_model(interactions)

                if not user_query:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'Please provide a query.')
                    return

                user_query = user_query.strip()

                if user_query.lower() in ["quit", "end", "stop", "bye", "goodbye"]:
                    response = respond_to_goodbye()
                elif user_query.lower() in ["hi", "hello", "hey", "what's up", "wassup", "howdy", "how are you"]:
                    response = respond_to_greeting()
                else:
                    context["last_query"] = user_query

                    special_response = handle_special_cases(user_query)
                    if special_response:
                        response = special_response
                        save_interaction(user_query, special_response)
                        context["last_response"] = special_response
                    elif detect_personal_info(user_query):
                        response = "Thank you for sharing that with me!"
                        save_interaction(user_query, response)
                        context["last_response"] = response
                    else:
                        sentiment = analyze_sentiment(user_query)
                        personalized_query = personalize_response(user_query, sentiment)
                        response = perform_search(personalized_query)

                        if not response or "Sorry" in response:
                            response = "Sorry, I couldn't find relevant information."
                        else:
                            is_question, is_list_request = analyze_query(personalized_query)
                            if is_list_request:
                                response = " ".join(response.split('. ')[:6])
                            elif is_question:
                                response = " ".join(response.split('. ')[:4])

                            response = construct_reply(response)

                save_interaction(user_query, response)
                context["last_response"] = response

                self.send_response(200)
                self.send_header('Content-type', 'application/json')  # Sending JSON response
                self.end_headers()
                self.wfile.write(json.dumps({"response": response}).encode('utf-8'))

            except ValueError as ve:
                print(f"Validation Error: {str(ve)}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(ve)}).encode())

            except Exception as e:
                print(f"Error: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Internal Server Error'}).encode())

    
    def log_message(self, format, *args):
        if debug_mode:
            super().log_message(format, *args)  # Call the superclass log_message for logging

def setup_logging():
    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create handlers
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatters and add them to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def start_server(server_address):
    global debug_mode
    interactions = load_interactions()
    train_model(interactions)
    
    httpd = HTTPServer(server_address, RequestHandler)
    try:
        if debug_mode:
            print('Starting server in debug mode on http://{}:{}/ ...'.format(*server_address))
        else:
            print('Starting server on http://{}:{}/ ...'.format(*server_address))
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.")


if __name__ == '__main__':
    debug_mode = True  # Set this to True for debug mode
    server_address = ('127.0.0.1', 5500)  # Change the port as needed

    if debug_mode:
        app.debug = True
        logger = setup_logging()
        app.logger.setLevel(logging.DEBUG)

    start_server(server_address)

    # Close the database connection when the server is stopped
    conn.close()
    
