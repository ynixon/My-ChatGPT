# export FLASK_DEBUG=development
# unset FLASK_DEBUG
# python chat.py --mode web
# python chat.py --mode console 
import os
import openai
from dotenv import load_dotenv
import argparse
from flask import Flask, redirect, request, render_template, session, jsonify, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import session
from datetime import datetime
import uuid

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
openai.api_base = os.getenv("OPENAI_API_BASE", None)
openai.api_version = os.getenv("OPENAI_API_VERSION", None)
openai.api_type = os.getenv("OPENAI_API_TYPE", None)
system_content = os.getenv("SYSTEM_CONTENT", None)

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


def process_message(text, session_id, sender, db=None):
    if app.debug:
        print(f"Processing message: {text}")
        print(f"Database object: {db}")
    with app.app_context():
        # Create the database tables
        db.create_all()
        if app.debug:
            print("Database tables created")
        text = text.replace("\"", "")
        message = Message(text=text, sender=sender, session=session_id)
        try:
            db.session.add(message)
            db.session.commit()
            messages = Message.query.all()
            if app.debug:
                print(f"Messages in database: {messages}")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding message to database: {e}")
            if "no such table" in str(e):
                db.create_all()
                db.session.add(message)
                db.session.commit()
                messages = Message.query.all()
                messages = Message.query.all()
                if app.debug:
                    print(f"Messages in database: {messages}")
        
        # Your custom logic for processing the text before generating a response
        # ...
        processed_text = text

    return processed_text


def conversation_history(session):
    conversation_history = Message.query.filter_by(
        session=session).order_by(Message.timestamp.asc()).all()
    return [message.to_dict() for message in conversation_history]


session_id = str(datetime.now().timestamp())


def clear_conversation(session_id, db=None):
    with app.app_context():
        messages = Message.query.filter_by(session=session_id).all()
        for message in messages:
            db.session.delete(message)
        db.session.commit()

def generate_response(user_input, session_id):
    messages = [
        {
            "role": "system",
            "content": system_content,
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

    if app.debug:
        print("generate_response Session ID: " + session_id)
        print(f"Generated response: {response_text}")

    return response_text

if args.mode == "web":
    @app.route('/')
    def index():
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        return render_template('index.html', session_id=session_id)

    @app.route('/chat_session')
    def get_chat_session():
        if 'session_id' not in session:
            new_session_id = str(uuid.uuid4())
            if app.debug:
                print("chat Session1 ID: " + new_session_id)
            session['session_id'] = new_session_id
        else:
            new_session_id = session['session_id']
            if app.debug:
                print("chat Session2 ID: " + new_session_id)
        return jsonify({'session_id': new_session_id})

    @app.route('/new_session', methods=['GET'])
    def new_session():
        if 'session_id' not in session:
            session_id = str(uuid.uuid4())
            print("new Session1 ID: " + session_id)
            session['session_id'] = session_id
        else:
            session_id = session['session_id']
            if app.debug:
                print("new Session2 Session ID: " + session_id)
        return jsonify({'session_id': session_id})

    @app.route('/message', methods=['POST'])
    def message():
        user_input = request.form['message']
        # session_id = request.form['session_id']  # Remove this line

        if app.debug:
            print("mes Session ID: " + session_id)  # Remove this line

        process_message(user_input, session_id, "user", db)

        response_text = generate_response(user_input, session_id)

        process_message(response_text, session_id, "assistant", db)

        return jsonify({'message': response_text})


    @app.route('/clear', methods=['POST'])
    def clear():
        session_id = request.form['session_id']
        clear_conversation(session_id, db)
        return jsonify({'status': 'success'})

    @app.route('/completion', methods=['POST'])
    def completion():
        if 'prompt' not in request.form:
            return jsonify({'error': 'Missing prompt in request form'}), 400

        prompt = request.form['prompt']
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        if app.debug:
            print("comp Session ID: " + session_id)
        response_text = generate_response(prompt, session_id)
        
        # Add this line to assign the sender as 'user'
        sender = 'user'

        # Pass the session_id variable to the process_message function
        processed_prompt = process_message(prompt, session_id, sender, db=db)

        return jsonify({'message': response_text})



    with app.app_context():
        if app.debug:
            print("Creating db")
        # Create the database tables
        db.create_all()

    if __name__ == '__main__':
        app.run(debug=True)

elif args.mode == "console":
    print("Starting console mode. Type 'exit' to quit.")

    with app.app_context():  # Add this line to avoid application context errors
        # Create a new session ID for the console mode
        session_id = str(uuid.uuid4())
        try:
            while True:
                user_input = input("You: ")
                if user_input.lower() == 'exit':
                    break

                # Process and save user message
                process_message(user_input, session_id, "user", db)

                # Generate assistant's response
                response_text = generate_response(user_input, session_id)
                print(f"Assistant: {response_text}")

                # Process and save assistant's response
                process_message(response_text, session_id, "assistant", db)
        except KeyboardInterrupt:
            print("\nExiting console mode.")

else:
    print("Error: Invalid mode specified. Must be 'web' or 'console'.")
