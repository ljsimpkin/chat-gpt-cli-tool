import openai
import os
import sys
import argparse
from colorama import Fore, Style

MODEL="gpt-3.5-turbo"
#MODEL="gpt-4-0613"

def concatenate_arguments(*args):
    return ' '.join(map(str, args))

def setup_openai():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environmental variable.")
    openai.api_key = api_key

def interact_with_gpt(messages, max_tokens=50):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages
    )
    return response['choices'][0]['message']['content'].strip()

def main():
    setup_openai()

    arguments = sys.argv[1:]
    prompt_args = concatenate_arguments(*arguments)

    if prompt_args:
        response = interact_with_gpt(messages=[{"role": "user", "content": prompt_args}])
        return print(response)
    
    print("Welcome to ChatGPT CLI. Type 'exit' to end the conversation.")
    
    conversation = []
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        conversation.append({"role": "user", "content": user_input})
        response = interact_with_gpt(messages=conversation)
        conversation.append({"role": "assistant", "content": response})
        print(Fore.GREEN + "ChatGPT: " + response + Style.RESET_ALL)

if __name__ == "__main__":
    main()
