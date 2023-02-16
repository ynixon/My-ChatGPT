from flask import Flask, request, jsonify
import openai, os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    return app

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data['message']
    response = {'response': 'Hello, you said: ' + message}
    return jsonify(response)

if __name__ == '__main__':
    app.run()
