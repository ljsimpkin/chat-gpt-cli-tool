from openai import OpenAI
from anthropic import Anthropic
import os
import argparse
import subprocess
from colorama import Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
import sys
import termios
import tty

openai_client = OpenAI()
anthropic_client = Anthropic()

MODEL="gpt-3.5-turbo"
MODEL_4="gpt-4-0125-preview"
CLAUDE_MODEL="claude-3-sonnet-20240229"
MAX_TOKENS=1000
TEMPERATURE=1

CODE_FLAG="You are a code generation assistant that only responds with raw code. Respond with the code in plain text format without tripple backricks. Output only the code and nothing else."
BASH_FLAG="You are a code generation assistant that only responds with raw code. Respond with the bash command in plain text format without tripple backricks. Output only the code and nothing else."

def concatenate_arguments(*args):
    return ' '.join(map(str, args))

def setup_api():
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not openai_key:
        raise ValueError("Please set the OPENAI_API_KEY environmental variable.")
    if not anthropic_key:
        raise ValueError("Please set the ANTHROPIC_API_KEY environmental variable.")
    openai_client.api_key = openai_key
    anthropic_client.api_key = anthropic_key

def interact_with_gpt(messages, use_claude=False):
    if use_claude:
        # Convert OpenAI-style messages to Anthropic format
        anthropic_messages = []
        system_message = None
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                anthropic_messages.append({"role": msg['role'], "content": msg['content']})
        
        response = anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            messages=anthropic_messages,
            system=system_message,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.content[0].text
    else:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content

def ask_execute_command(command):
    print(f"\nPress 'y' or 'Enter' to execute, any other key to cancel.\n")
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return key.lower() == 'y' or key == '\r'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", nargs="*", help="Output")
    parser.add_argument("-b", nargs="*", help="Output")
    parser.add_argument("-m", "--model", action="store_true", help=f"Toggle model to load {MODEL_4}")
    parser.add_argument("--claude", action="store_true", help="Use Claude by Anthropic")
    parser.add_argument("text", nargs="*", help="Text to send to the AI model")
    args = parser.parse_args()

    global MODEL
    if args.model:
        MODEL = MODEL_4

    setup_api()

    use_claude = args.claude

    if args.c:
        prompt_args = concatenate_arguments(*args.c)
        input_messages=[{'role':'system', 'content': CODE_FLAG}, {"role": "user", "content": prompt_args}]
        response = interact_with_gpt(messages=input_messages, use_claude=use_claude)
        print(response)
        return

    if args.b:
        prompt_args = concatenate_arguments(*args.b)
        input_messages=[{'role':'system', 'content': BASH_FLAG}, {"role": "user", "content": prompt_args}]
        response = interact_with_gpt(messages=input_messages, use_claude=use_claude)
        print(Fore.RED + response + Style.RESET_ALL)
        if ask_execute_command(response):
            try:
                subprocess.run(response, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Command execution failed: {e}")
        return

    prompt_args = concatenate_arguments(*args.text)

    if prompt_args:
        response = interact_with_gpt(messages=[{"role": "user", "content": prompt_args}], use_claude=use_claude)
        print(response)
        return

    model_name = CLAUDE_MODEL if use_claude else MODEL
    print(Fore.YELLOW + f"Welcome to AI CLI. Type 'exit' to end the conversation. Using model: {model_name}" + Style.RESET_ALL)
    
    conversation = []
    history = InMemoryHistory()
    while True:
        user_input = prompt("You: ", history=history)
        if user_input.lower() == 'exit':
            break

        conversation.append({"role": "user", "content": user_input})
        response = interact_with_gpt(messages=conversation, use_claude=use_claude)
        conversation.append({"role": "assistant", "content": response})
        print(Fore.YELLOW + "AI: " + response + Style.RESET_ALL)

if __name__ == "__main__":
    main()

