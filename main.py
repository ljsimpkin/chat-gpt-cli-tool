from openai import OpenAI
import os
import argparse
from colorama import Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
import pyperclip
import sys

openai_client = OpenAI()

MODEL="gpt-4o-mini"
MODEL_4="gpt-4o"
MAX_TOKENS=1000
TEMPERATURE=1

CODE_FLAG="You are a code generation assistant that only responds with raw code. Respond with the code in plain text format without tripple backricks and without comments. Output only the code and nothing else."

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
    if stream:
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
    else:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", nargs="*", help="Output")
    parser.add_argument("-m", "--model", action="store_true", help=f"Toggle model to load {MODEL_4}")
    parser.add_argument("text", nargs="*", help="Text to send to the AI model")
    args = parser.parse_args()

    global MODEL
    if args.model:
        MODEL = MODEL_4

    setup_api()

    # Check for piped input
    stdin_data = None
    if check_stdin():
        stdin_data = read_stdin()

    if args.c:
        prompt_args = concatenate_arguments(*args.c)
        input_messages=[{'role':'system', 'content': CODE_FLAG}, {"role": "user", "content": prompt_args}]
        response = interact_with_gpt(messages=input_messages, stream=False)
        print(Fore.YELLOW + response + Style.RESET_ALL)
        try:
            pyperclip.copy(response)
            print("\nCopied to clipboard!")
        except pyperclip.PyperclipException:
            print(Fore.RED + "\nFailed to copy to clipboard. Make sure you have the required dependencies installed." + Style.RESET_ALL)
        return

    prompt_args = concatenate_arguments(*args.text)

    # Handle piped input combined with command line arguments
    if stdin_data:
        if prompt_args:
            # Combine stdin data with command line arguments
            full_prompt = f"{prompt_args}\n\n{stdin_data}"
        else:
            full_prompt = stdin_data
        
        # Initialize conversation with piped data
        conversation = [{"role": "user", "content": full_prompt}]
        print(Fore.YELLOW + "\nAI: " + Style.RESET_ALL, end='')
        response = interact_with_gpt(messages=conversation, stream=True)
        conversation.append({"role": "assistant", "content": response})
        
        # Continue with conversation mode
        print(Fore.YELLOW + f"\nContinuing in conversation mode. Type 'exit' to end the conversation. Using model: {MODEL}" + Style.RESET_ALL)
        history = InMemoryHistory()
        while True:
            user_input = prompt("You: ", history=history)
            if user_input.lower() == 'exit':
                break

            conversation.append({"role": "user", "content": user_input})
            print(Fore.YELLOW + "\nAI: " + Style.RESET_ALL, end='')
            response = interact_with_gpt(messages=conversation, stream=True)
            conversation.append({"role": "assistant", "content": response})
        
        return

    if prompt_args:
        response = interact_with_gpt(messages=[{"role": "user", "content": prompt_args}], stream=False)
        print(response)
        return

    print(Fore.YELLOW + f"Welcome to AI CLI. Type 'exit' to end the conversation. Using model: {MODEL}" + Style.RESET_ALL)
    
    conversation = []
    history = InMemoryHistory()
    while True:
        user_input = prompt("You: ", history=history)
        if user_input.lower() == 'exit':
            break

        conversation.append({"role": "user", "content": user_input})
        print(Fore.YELLOW + "\nAI: " + Style.RESET_ALL, end='')
        response = interact_with_gpt(messages=conversation, stream=True)
        conversation.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()

