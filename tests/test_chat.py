from contextlib import redirect_stdout
import argparse
import unittest
import os
from unittest.mock import patch, MagicMock
from io import StringIO
from dotenv import load_dotenv
import openai
from app import app 
from app import create_app

load_dotenv()

def run_chatbot():
    # Get the arguments
    parser = argparse.ArgumentParser(description='OpenAI Chatbot')
    parser.add_argument('--model', required=True, help='OpenAI API model name')
    parser.add_argument('--key', required=True, help='OpenAI API key')
    parser.add_argument('--type', required=True, help='OpenAI API type')
    parser.add_argument('--base', required=True, help='OpenAI API base')
    parser.add_argument('--version', required=True, help='OpenAI API version')
    parser.add_argument('--mode', required=True, choices=['console', 'web'], help='Chatbot mode')
    args = parser.parse_args()

    # Set the OpenAI environment variables
    os.environ["OPENAI_MODEL"] = args.model
    os.environ["OPENAI_API_KEY"] = args.key

    if args.mode == 'console':
        # Run the console mode
        while True:
            prompt = input("You: ")
            if prompt.lower() == "quit":
                break

            # Call the OpenAI API to get a response
            response = openai.Completion.create(
                engine=args.model,
                prompt=prompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.7,
            )

            # Print the response
            print("Chatbot:", response.choices[0]['text'])


    elif args.mode == 'web':
        # Run the web mode
        pass  # TODO: Implement the web mode

class TestOpenAIConsole(unittest.TestCase):
    @patch("builtins.input", side_effect=["Hello, world", "quit"])
    def test_console(self, mock_input):
        # Mock the OpenAI Completion API
        mock_completion = MagicMock()
        mock_completion.choices = [
            {
                "text": "Hello, world! How are you doing today?"
            }
        ]
        with patch("openai.Completion.create", return_value=mock_completion):
            # Redirect stdout to capture console output
            output = StringIO()
            # Provide required arguments to run_chatbot()
            args = argparse.Namespace(model=os.getenv("OPENAI_MODEL"), key=os.getenv("OPENAI_API_KEY"), mode="console", type=os.getenv("OPENAI_API_TYPE"), base=os.getenv("OPENAI_API_BASE"), version=os.getenv("OPENAI_API_VERSION"))
            with redirect_stdout(output):
                # Run the console mode
                with patch('argparse.ArgumentParser.parse_args', return_value=args):
                    run_chatbot()
        self.assertIn("Hello, world! How are you doing today?", output.getvalue())

class TestOpenAIWeb(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.test_client = self.app.test_client()

    def test_web(self):
        with app.test_client() as client:
            data = {'message': 'Hello'}
            response = client.post('/chat', json=data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['response'], 'Hello, you said: Hello')

if __name__ == '__main__':
    unittest.main()
