from openai import OpenAI
import os
import argparse
import subprocess
from colorama import Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
import sys
import termios
import tty

client = OpenAI()

MODEL="gpt-3.5-turbo"
MODEL_4="gpt-4-0125-preview"
MAX_TOKENS=None
TEMPERATURE=1

CODE_FLAG="You are a code generation assistant that only responds with raw code. Respond with the code in plain text format without tripple backricks. Output only the code and nothing else."

def concatenate_arguments(*args):
    return ' '.join(map(str, args))

def setup_openai():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environmental variable.")
    client.api_key = api_key

def interact_with_gpt(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content

def ask_execute_command(command):
    print(f"\nDo you want to execute this command in bash? (Press 'y' or Enter to execute, any other key to cancel)")
    print(f"Command: {command}")
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    print()  # Print a newline for better formatting
    return key.lower() == 'y' or key == '\r'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", nargs="*", help="Output")
    parser.add_argument("-m", "--model", action="store_true", help=f"Toggle model to load {MODEL_4}")
    parser.add_argument("text", nargs="*", help="Text to send to ChatGPT")
    args = parser.parse_args()

    global MODEL
    if args.model:
        MODEL = MODEL_4

    setup_openai()

    if args.c:
        prompt_args = concatenate_arguments(*args.c)
        input_messages=[{'role':'system', 'content': CODE_FLAG}, {"role": "user", "content": prompt_args}]
        response = interact_with_gpt(messages=input_messages)
        print(response)
        if ask_execute_command(response):
            try:
                subprocess.run(response, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Command execution failed: {e}")
        return

    prompt_args = concatenate_arguments(*args.text)

    if prompt_args:
        response = interact_with_gpt(messages=[{"role": "user", "content": prompt_args}])
        print(response)
        return

    print(Fore.YELLOW + "Welcome to ChatGPT CLI. Type 'exit' to end the conversation. Using model: " + MODEL + Style.RESET_ALL)
    
    conversation = []
    history = InMemoryHistory()
    while True:
        user_input = prompt("You: ", history=history)
        if user_input.lower() == 'exit':
            break

        conversation.append({"role": "user", "content": user_input})
        response = interact_with_gpt(messages=conversation)
        conversation.append({"role": "assistant", "content": response})
        print(Fore.YELLOW + "ChatGPT: " + response + Style.RESET_ALL)

if __name__ == "__main__":
    main()

