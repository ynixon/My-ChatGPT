import os
import openai
from dotenv import load_dotenv
import argparse

load_dotenv()

openai.api_type = os.getenv("OPENAI_API_TYPE")
if openai.api_type == "azure":
    openai.api_version = os.getenv("OPENAI_API_VERSION")
    openai.api_base = os.getenv("OPENAI_API_BASE")

if "OPENAI_MODEL" not in os.environ:
    raise ValueError("Error: OPENAI_MODEL is not set in the environment")
if "OPENAI_API_KEY" not in os.environ:
    raise ValueError("Error: OPENAI_API_KEY is not set in the environment")

model = os.getenv("OPENAI_MODEL")
openai.api_key = os.getenv("OPENAI_API_KEY")

if openai.api_type == "azure" and (not openai.api_base or not openai.api_version):
    print("Error: OPENAI_API_BASE and OPENAI_API_VERSION must be set when using the azure API type.")
elif not openai.api_key:
    print("Error: OPENAI_API_KEY must be set.")
else:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", help="Set the application mode", choices=["console", "web"])
    args = parser.parse_args()

    if args.mode == "web":
        from flask import Flask, request, render_template, session, jsonify

        app = Flask(__name__)
        app.secret_key = os.urandom(24)

        def process_message(prompt, response, session):
            conversation_history = session.get('conversation_history', [])
            conversation_history = [(prompt, response)] + conversation_history
            session['conversation_history'] = conversation_history
            return conversation_history

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/static/<path:path>')
        def static_file(path):
            return app.send_static_file(path)

        @app.route('/completion', methods=['POST'])
        def completion():
            prompt = request.form['prompt']
            completion = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.5,
            )
            response = completion['choices'][0]['text'].strip()
            print("Session data before processing message:", session)
            session['conversation_history'] = process_message(
                prompt, response, session)
            print("Session data after processing message:", session)
            return jsonify({"conversation_history": session['conversation_history']})

        if __name__ == '__main__':
            app.run(debug=True)

    elif args.mode == "console":
        try:
            prompt = input("Enter a prompt: ")
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.5,
            )
            text = response['choices'][0]['text']
            lines = text.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            formatted_text = '\n'.join(lines)
            print(formatted_text)
        except openai.error.AuthenticationError:
            print("Error: Invalid API key.")
        except Exception as e:
            print("An error occurred:", e)
    else:
        print("Error: Invalid mode specified. Must be 'web' or 'console'.")
