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
            message.timestamp = datetime.fromisoformat(message_dict['timestamp'])
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

        # fetch the latest 3 messages from the database and append them to the prompt
        conversation_history = Message.query.filter_by(session=session).order_by(Message.timestamp.desc()).limit(3).all()
        for i in range(len(conversation_history)):
            #conversation_history[i].text = conversation_history[i].text.replace("\"", "\\\"")
            conversation_history[i].text = conversation_history[i].text.replace("\"", "")

        #conversation_history.reverse()  # reverse the order to get the most recent messages last
        prompt_lines = []
        response_lines = []
        for message in conversation_history:
            response_lines.append(message.text)
        if message.text not in response_lines and sender == 'user':
            prompt_with_history = " !$ ".join(prompt_lines + response_lines + [''])
        else:
            prompt_with_history = " !$ ".join(response_lines + [''])

        # Append the prompt or response based on the sender
        # if sender == 'user':
        #     prompt_with_history += f"\n{text}"
        # elif sender == 'chatbot':
        #     prompt_with_history += f"\n# {text}"

        return prompt_with_history


    
    with app.app_context():
        # Create the database tables
        db.create_all()

    # @app.errorhandler(Exception)
    # def handle_error(error):
    #     # Log the error to the console or to a file
    #     print(f"An error occurred: {str(error)}")
    
    #     # Render a custom error page
    #     return render_template("index.html", error=str(error))

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

            # Get the conversation history from the database
            conversation_history = Message.query.filter_by(session=session).order_by(Message.timestamp.desc()).all()

            # Get the most recent user message from the conversation history
            last_user_message = None
            for message in reversed(conversation_history):
                if message.sender == 'user':
                    last_user_message = message.text
                    break

            # Construct the prompt based on the conversation history and the current user input
            prompt_lines = []
            response_lines = []
            for message in conversation_history:
                if message.sender == 'user':
                    prompt_lines.append(message.text)
                else:
                    response_lines.append(message.text)
            if last_user_message is not None and last_user_message not in prompt_lines:
                prompt_lines.append(" !$ ".join(last_user_message + ['']))
            prompt_with_history = " !$ ".join(response_lines + prompt_lines + [prompt] + [''])

            process_message(prompt, session, 'user')
            print('prompt_with_history: ' + prompt_with_history)

            # Generate response using OpenAI API
            completion = openai.Completion.create(
                engine=model,
                prompt=prompt_with_history,
                max_tokens=1024,
                n=1,
                stop='!$',
                temperature=0.5
            )

            # Get the chatbot response from the OpenAI API
            # print(completion)
            response = completion.choices[0].text.strip()

            # Call process_message to save the chatbot response to the conversation history
            process_message(response, session, 'chatbot')

            response = response.replace("<code>", "<pre><code>")
            response = response.replace("</code>", "</code></pre>")

            response = "'''" + response + "'''"
            # print(response)

            return jsonify({'response': response})
        
        except Exception as e:
            # Log the error to the console or to a file
            print(f"An error occurred: {str(e)}")
            
            # Redirect to the index page with an error message in the query string
            # return redirect(url_for("index", error=str(e)))
            return jsonify({'success': False, 'error': str(e)})

    if __name__ == '__main__':
        app.run(debug=True)

elif args.mode == "console":
    prompt = input("Enter a prompt: ")
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    text = response.choices[0].text
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    formatted_text = '\n'.join(lines)
    print(formatted_text)

else:
    print("Error: Invalid mode specified. Must be 'web' or 'console'.")
