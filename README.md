# My-ChatGPT




A simple Flask web app that uses OpenAI's language model API to generate text completions for a given prompt. The app implements a basic chatbot interface that allows users to type in questions and receive answers.

## Getting Started

1. Clone the repository:

```console

git clone https://github.com/ynixon/My-ChatGPT.git

```

2. Create a virtual environment and activate it:

```console

python3 -m venv venv

source venv/bin/activate

```

3. Install the required packages:

```console

pip install -r requirements.txt

```

4. Create a .env file in the project root directory and set your OpenAI API key:

```console

OPENAI_API_KEY=your_api_key

```

5. Run the app:

```console

python chat.py

```

The app should now be running at http://localhost:5000.

## Usage

1. Type a prompt in the input field and press the "Submit" button.

2. The app will use OpenAI's language model API to generate a response to your prompt.

3. The conversation history will be displayed below the input field, displaying both the prompt and the response.

## Note

The model used in this app is set to "text-davinci-002", but you can change it to any other OpenAI language model that you have access to.
