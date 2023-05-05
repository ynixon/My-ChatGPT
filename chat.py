import os
import openai
from dotenv import load_dotenv
import argparse
from flask import Flask, redirect, request, render_template, session, jsonify, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
openai.api_base = os.getenv("OPENAI_API_BASE", None)
openai.api_version = os.getenv("OPENAI_API_VERSION", None)
openai.api_type = os.getenv("OPENAI_API_TYPE", None)

if not openai.api_key:
    raise ValueError("Error: OPENAI_API_KEY must be set.")
if not model:
    raise ValueError("Error: OPENAI_MODEL is not set in the environment.")

parser = argparse.ArgumentParser()
parser.add_argument(
    "--mode", help="Set the application mode", choices=["console", "web"])
args = parser.parse_args()

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)


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


def process_message(text, session, sender, db=None):
    with app.app_context():
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


def conversation_history(session):
    conversation_history = Message.query.filter_by(
        session=session).order_by(Message.timestamp.asc()).all()
    return [message.to_dict() for message in conversation_history]


session_id = str(datetime.now().timestamp())

if args.mode == "web":
    @app.route('/')
    def index():
        return render_template('index.html', conversation_history=conversation_history(session_id))

    @app.route('/message', methods=['POST'])
    def message():
        user_input = request.form['message']
        process_message(user_input, session_id, "user", db)
        response = openai.Completion.create(
            engine=model,
            prompt=f"{user_input.strip()}",
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.7,
        )
        message = response.choices[0].text.strip()
        process_message(message, session_id, "chatbot", db)
        return jsonify({'response': message})

    @app.route('/clear')
    def clear():
        db.session.query(Message).filter_by(session=session_id).delete()
        db.session.commit()
        return redirect(url_for('index'))

    @app.route('/completion', methods=['POST'])
    def handle_completion():
        prompt = request.form['prompt']
        process_message(prompt, session_id, 'user', db)

        conversation_history_list = conversation_history(session_id)

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

        for message in conversation_history_list:
            messages.append({
                "role": "user" if message['sender'] == "user" else "assistant",
                "content": message['text']
            })

        response = openai.ChatCompletion.create(
            engine=model,
            messages=messages,
            temperature=0.5,
            max_tokens=350,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        response_text = response.choices[0].message.content.strip()
        process_message(response_text, session_id, 'assistant', db)

        return jsonify({'response': response_text})

    with app.app_context():
        # Create the database tables
        db.create_all()

    if __name__ == '__main__':
        app.run(debug=True)

# Console mode and other code remains the same


elif args.mode == "console":
    print("Starting console mode. Type 'exit' to quit.")

    with app.app_context():  # Add this line
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            process_message(user_input, session_id, "user", db)

            messages = [
                {
                    "role": "system",
                    "content": "You are Quest customer support whose primary goal is to help users with issues they are experiencing with their Foglight. You are friendly and concise. You only provide factual answers to queries, and do not provide answers that are not related to Foglight.",
                },
                {
                    "role": "user",
                    "content": user_input,
                },
            ]
            conversation_history_list = conversation_history(session_id)
            for message in conversation_history_list:
                messages.append({
                    "role": "user" if message['sender'] == "user" else "assistant",
                    "content": message['text']
                })

            response = openai.ChatCompletion.create(
                engine=model,
                messages=messages,
                temperature=0.5,
                max_tokens=350,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            response_text = response.choices[0].message.content.strip()
            print(f"Assistant: {response_text}")
            process_message(response_text, session_id, "assistant", db)
else:
    print("Error: Invalid mode specified. Must be 'web' or 'console'.")
