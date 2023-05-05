# My-ChatGPT

A simple Flask web app and console application that uses OpenAI's language model API to generate text completions for a given prompt. The app implements a basic chatbot interface that allows users to type in questions and receive answers.

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

4. Create a .env file in the project root directory and make sure to set the required environment variables in the .env file:

```console
OPENAI_API_KEY=your_api_key
OPENAI_API_TYPE=[azure|openai]
OPENAI_API_BASE=https://<Azure OpenAI Cognitive Service name>.openai.azure.com/
OPENAI_API_VERSION=2023-03-15-preview
OPENAI_MODEL=gpt-35-turbo
SYSTEM_CONTENT="The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly."

```

- `OPENAI_API_KEY`: Your OpenAI API key. You can generate an API key in the - OpenAI web interface. See https://onboard.openai.com for details, or email support@openai.com if you have any questions.
- `OPENAI_API_TYPE`: The type of OpenAI API. Set to azure if using the Azure API, or openai if using the OpenAI API.
- `OPENAI_API_BASE`: The base URL of the OpenAI API. Required if `OPENAI_API_TYPE` is set to azure.
- `OPENAI_API_VERSION`: The version of the OpenAI API to use. Required if `OPENAI_API_TYPE` is set to azure.
- `OPENAI_MODEL`: The name of the OpenAI GPT model to use.
- `SYSTEM_CONTENT`: The system content message for setting the context of the conversation.

5. Run the Flask app or Console app:

```console
# Flask app
python chat.py --mode web

# Console app
python chat.py --mode console

```

## Usage

1. For Flask app, navigate to http://localhost:5000. For Console app, type your prompt in the console.

2. The app will use OpenAI's language model API to generate a response to your prompt.

3. The conversation history will be displayed for Flask app or printed to the console for Console app, displaying both the prompt and the response.

## Note

The model used in this app is set to "gpt-35-turbo", but you can change it to any other OpenAI language model that you have access to.
