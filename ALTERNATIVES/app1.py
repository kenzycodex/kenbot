from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
import json
import mysql.connector
import hashlib
from base64 import b64decode
import requests
from bs4 import BeautifulSoup
import re

# Set debug mode to True to enable debugging
debug_mode = True

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

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = urlparse(self.path).path
        if url_path == '/':
            url_path = '/signup.html'
        file_path = './' + url_path.lstrip('/')
        if os.path.exists(file_path):
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
                username = params.get('username', '')
                password = params.get('password', '')

                if not (username and password):
                    raise ValueError("Username and password are required")

                hashed_password = hashlib.sha256(password.encode()).hexdigest()

                cursor.execute("SELECT * FROM kendata WHERE username = %s AND password = %s", (username, hashed_password))
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
                    self.wfile.write(json.dumps({'error': 'Invalid username or password'}).encode())

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
        
        elif self.path == '/search':
            try:
                params = json.loads(post_data)
                query = params.get('query', '')

                if not query:
                    raise ValueError("Query is required")

                # Perform the search using Bing
                url = f'https://www.bing.com/search?q={query}'
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                results = []
                for item in soup.select('li.b_algo'):
                    title = item.find('h2').text
                    link = item.find('a')['href']
                    snippet = item.find('p').text if item.find('p') else ''
                    # Remove "WEB" and dates from snippets
                    cleaned_snippet = re.sub(r'WEB|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '', snippet)
                    results.append({'title': title, 'link': link, 'snippet': cleaned_snippet.strip()})
                
                # Extract important sentences (e.g., first snippet of each result)
                cleaned_results = [result['snippet'] for result in results if result['snippet']]
                summary = ' '.join(cleaned_results[:2])  # Take only the first 2 snippets for brevity

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'summary': summary}).encode())

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
            super().log_message(format, *args)

if __name__ == '__main__':
    server_address = ('127.0.0.1', 5500)
    httpd = HTTPServer(server_address, RequestHandler)
    
    try:
        if debug_mode:
            print('Starting server in debug mode on http://{}:{}/ ...'.format(*server_address))
        else:
            print('Starting server on http://{}:{}/ ...'.format(*server_address))
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    
    # Close the database connection when the server is stopped
    conn.close()