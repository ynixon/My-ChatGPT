import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
openai.api_base = os.getenv("OPENAI_API_BASE", None)
openai.api_version = os.getenv("OPENAI_API_VERSION", None)
openai.api_type = os.getenv("OPENAI_API_TYPE")

if not openai.api_key:
    raise ValueError("Error: OPENAI_API_KEY must be set.")
if not model:
    raise ValueError("Error: OPENAI_MODEL is not set in the environment.")


response = openai.Completion.create(
    engine=model,
    prompt="I live in israel !$ What is my name ? !$ are you sure? !$ Oh, right. I forgot. Thanks for remembering, AI! !$ Yes, I'm sure. You've told me before that your name is Yossi. !$ Are you sure? !$ My name is Yossi. !$ What is my name? !$ Your name is not provided. !$ Your name is Yossi. !$ Your name is Yossi. !$ Yes, I'm sure. You've told me before that your name is Yossi. !$ Your name is Yossi. !$ Your name is Yossi. !$ Yes, I'm sure. You've told me before that your name is Yossi. !$ my name is yossi !$ Yes, I am sure. !$ Your name is not provided. !$ Your name is not provided. !$ Where do i live? !$ ",
    max_tokens=256,
    stop='!$',
    temperature=0.5,
)

text = response.choices[0].text
lines = text.split('\n')
lines = [line.strip() for line in lines if line.strip()]
formatted_text = '\n'.join(lines)
print(formatted_text)
