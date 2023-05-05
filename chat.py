import os
import openai
from dotenv import load_dotenv
import argparse
from flask import Flask, redirect, request, render_template, session, jsonify, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import subprocess

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
openai.api_base = os.getenv("OPENAI_API_BASE", None)
openai.api_version = os.getenv("OPENAI_API_VERSION", None)
openai.api_version = "2023-03-15-preview"
openai.api_type = os.getenv("OPENAI_API_TYPE", None)

if not openai.api_key:
    raise ValueError("Error: OPENAI_API_KEY must be set.")
if not model:
    raise ValueError("Error: OPENAI_MODEL is not set in the environment.")

parser = argparse.ArgumentParser()
parser.add_argument(
    "--mode", help="Set the application mode", choices=["console", "web"])
args = parser.parse_args()

if args.mode == "web":
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    app.config["OPENAI_MODEL"] = model

    # create a SQLAlchemy object and configure the app to use it
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversation.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    # define a model for the conversation history table
    class Message(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        text = db.Column(db.String(1024))
        sender = db.Column(db.String(10))
        timestamp = db.Column(db.DateTime)
        session = db.Column(db.String(36))

        def __init__(self, text, sender, session):
            self.text = text
            self.sender = sender
            self.timestamp = datetime.now()
            self.session = session

        def to_dict(self):
            return {
                'text': self.text,
                'sender': self.sender,
                'timestamp': self.timestamp.isoformat(),
                'session': self.session,
            }

        @classmethod
        def from_dict(cls, message_dict):
            message = cls(
                text=message_dict['text'],
                sender=message_dict['sender'],
                session=message_dict['session']
            )
            message.timestamp = datetime.fromisoformat(
                message_dict['timestamp'])
            return message

    def message_to_dict(message):
        return {'id': message.id, 'session': message.session, 'text': message.text}

    def process_message(text, session, sender):
        # create a new message object and save it to the database
        text = text.replace("\"", "")
        message = Message(text=text, sender=sender, session=session)
        try:
            db.session.add(message)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if "no such table" in str(e):
                db.create_all()
                db.session.add(message)
                db.session.commit()

    with app.app_context():
        # Create the database tables
        db.create_all()

    @app.route('/')
    def index():
        error = request.args.get("error")
        return render_template("index.html", error=error)

    @app.route('/static/<path:path>')
    def static_file(path):
        return app.send_static_file(path)


    @app.route('/completion', methods=['POST'])
    def handle_completion(session=None):
        try:
            prompt = request.form['prompt']
            sender = 'user'
            if session is None:
                session = app.secret_key

            # Call process_message to save the user input to the conversation history
            process_message(prompt, session, 'user')

            # Get the conversation history from the database
            conversation_history = Message.query.filter_by(
                session=session).order_by(Message.timestamp.asc()).all()

            # Prepare messages for the Chat API
            messages = [
                {
                    "role": "system",
                    "content": "You are Quest customer support whose primary goal is to help users with issues they are experiencing with their Foglight. You are friendly and concise. You only provide factual answers to queries, and do not provide answers that are not related to Foglight.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]

            for message in conversation_history:
                messages.append({
                    "role": "user" if message.sender == "user" else "assistant",
                    "content": message.text
                })

            # print(messages)

            response = openai.ChatCompletion.create(
                engine=model,
                messages=messages,
                temperature=0.5,
                max_tokens=350,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            # print (response)

            # Get the assistant response from the OpenAI API
            response_text = response['choices'][0]['message']['content'].strip()

            # Call process_message to save the assistant response to the conversation history
            process_message(response_text, session, 'assistant')

            response_text = response_text.replace("<code>", "<pre><code>")
            response_text = response_text.replace("</code>", "</code></pre>")

            response_text = "'''" + response_text + "'''"

            print(f"User prompt: {prompt}")
            print(f"assistant response: {response_text}")

            return jsonify({'response': response_text})

        except Exception as e:
            # Log the error to the console or to a file
            print(f"An error occurred: {str(e)}")

            # Redirect to the index page with an error message in the query string
            return jsonify({'success': False, 'error': str(e)})

    if __name__ == '__main__':
        app.run(debug=True)


elif args.mode == "console":
    prompt = input("Enter a prompt: ")
    messages = [
        {
            "role": "system",
            "content": "You are Quest customer support whose primary goal is to help users with issues they are experiencing with their Foglight. You are friendly and concise. You only provide factual answers to queries, and do not provide answers that are not related to Foglight.",
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]
    response = openai.ChatCompletion.create(
        engine=model,
        messages=messages,
        temperature=0.5,
        max_tokens=350,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    # print(response)
    text = response['choices'][0]['message']['content'].strip()
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    formatted_text = '\n'.join(lines)
    print(formatted_text)

else:
    print("Error: Invalid mode specified. Must be 'web' or 'console'.")
