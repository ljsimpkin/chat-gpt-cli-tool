from openai import OpenAI
import os
import argparse
from colorama import Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
import pyperclip
import sys
import json  # Import the json module

openai_client = OpenAI()

MODEL = "gpt-4o-mini"
MODEL_4 = "gpt-4o"
MAX_TOKENS = 1000
TEMPERATURE = 1

HISTORY_FILE = ".ai_cli_history.json"

CODE_FLAG = "You are a code generation assistant that only responds with raw code. Respond with the code in plain text format without triple backticks and without comments. Output only the code and nothing else."


def concatenate_arguments(*args):
    return ' '.join(map(str, args))


def setup_api():
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("Please set the OPENAI_API_KEY environmental variable.")
    openai_client.api_key = openai_key


def check_stdin():
    """Check if there's data being piped to stdin"""
    return not sys.stdin.isatty()


def read_stdin():
    """Read all data from stdin"""
    return sys.stdin.read().strip()


def interact_with_gpt(messages, stream=False):
    """Interacts with the GPT model and returns the response."""
    if stream:
        return interact_with_gpt_stream(messages)
    else:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content


def interact_with_gpt_stream(messages):
    """Handles streaming responses from the GPT model."""
    stream_response = openai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        stream=True
    )

    collected_chunks = []
    for chunk in stream_response:
        if chunk.choices[0].delta.content:
            chunk_content = chunk.choices[0].delta.content
            print(Fore.YELLOW + chunk_content, end='', flush=True)
            collected_chunks.append(chunk_content)
    print()  # New line after streaming completes
    return ''.join(collected_chunks)


def load_history():
    """Load conversation history from file."""
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_history(conversation):
    """Save conversation history to file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(conversation, f)


def copy_to_clipboard(text):
    """Copies the given text to the clipboard."""
    try:
        pyperclip.copy(text)
        print("\nCopied to clipboard!")
    except pyperclip.PyperclipException:
        print(Fore.RED + "\nFailed to copy to clipboard. Make sure you have the required dependencies installed." + Style.RESET_ALL)


def handle_code_output(args):
    """Handles the code output mode."""
    prompt_args = concatenate_arguments(*args.c)
    input_messages = [{'role': 'system', 'content': CODE_FLAG}, {"role": "user", "content": prompt_args}]
    response = interact_with_gpt(messages=input_messages, stream=False)
    print(Fore.YELLOW + response + Style.RESET_ALL)
    copy_to_clipboard(response)


def handle_conversation(conversation, stream=False):
    """Handles the conversation with the AI model."""
    while True:
        user_input = prompt("You: ", history=InMemoryHistory())
        if user_input.lower() == '/exit':
            print("Exiting conversation.")
            break

        conversation.append({"role": "user", "content": user_input})
        print(Fore.YELLOW + "\nAI: " + Style.RESET_ALL, end='')
        response = interact_with_gpt(messages=conversation, stream=stream)
        conversation.append({"role": "assistant", "content": response})
        save_history(conversation)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", nargs="*", help="Output code and copy to clipboard")
    parser.add_argument("-m", "--model", action="store_true", help=f"Toggle model to load {MODEL_4}")
    parser.add_argument("-r", "--restore", action="store_true", help="Restore conversation, continuing from previous conversation.")
    parser.add_argument("text", nargs="*", help="Text to send to the AI model")
    args = parser.parse_args()

    global MODEL
    if args.model:
        MODEL = MODEL_4

    setup_api()
    conversation = load_history()

    if args.c:
        handle_code_output(args)
        return

    stdin_data = None
    if check_stdin():
        stdin_data = read_stdin()

    prompt_args = concatenate_arguments(*args.text)

    if stdin_data or prompt_args:
        full_prompt = f"{prompt_args}\n\n{stdin_data}" if prompt_args and stdin_data else (prompt_args or stdin_data)
        conversation.append({"role": "user", "content": full_prompt})
        print(Fore.YELLOW + "\nAI: " + Style.RESET_ALL, end='')
        response = interact_with_gpt(messages=conversation, stream=True)
        conversation.append({"role": "assistant", "content": response})
        save_history(conversation)

        if not args.interactive:
            return  # Exit after processing stdin and/or command line args

    if args.interactive:
        if sys.stdin.isatty():
            handle_conversation(conversation, stream=True)
        else:
            print(Fore.RED + "No interactive terminal available." + Style.RESET_ALL)
        return

    print(Fore.YELLOW + f"Welcome to AI CLI. Type 'exit' to end the conversation. Using model: {MODEL}" + Style.RESET_ALL)
    handle_conversation(conversation, stream=True)


if __name__ == "__main__":
    main()

