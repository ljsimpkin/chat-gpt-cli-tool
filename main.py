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

CODE_REVIEW_SYSTEM_PROMPT = """You are an expert code reviewer with years of experience in identifying potential issues, security vulnerabilities, and areas for improvement in code. When reviewing code, focus on the following:

*   **Best Practices:** Ensure the code adheres to established coding standards and best practices for the language and framework being used.
*   **Readability:** Assess the code's clarity and ease of understanding. Suggest improvements to variable names, comments, and overall structure to enhance readability.
*   **Efficiency:** Analyze the code for potential performance bottlenecks or inefficiencies. Recommend optimizations to improve execution speed and resource utilization.
*   **Security:** Identify any potential security vulnerabilities, such as SQL injection, cross-site scripting (XSS), or insecure data handling practices.
*   **Error Handling:** Evaluate the code's robustness in handling errors and exceptions. Suggest improvements to error messages, logging, and recovery mechanisms.
*   **Maintainability:** Consider the long-term maintainability of the code. Suggest improvements to modularity, testability, and documentation to facilitate future modifications and enhancements.
*   **Testability:** Ensure the code is easily testable and suggest improvements to facilitate unit testing, integration testing, and other forms of testing.
*   **Code Style:** Provide feedback on code style, including indentation, spacing, and naming conventions, to ensure consistency and adherence to established guidelines.

Provide specific and actionable recommendations for improving the code based on these criteria. Explain the reasoning behind your suggestions and provide examples where appropriate."""


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


def handle_conversation(conversation, stream=False, code_review=False):
    """Handles the conversation with the AI model."""
    if code_review and not conversation:
        conversation.append({"role": "system", "content": CODE_REVIEW_SYSTEM_PROMPT})

    while True:
        user_input = prompt("You: ", history=InMemoryHistory())
        normalized_input = user_input.strip().lower()
        if normalized_input in ('/exit', 'exit', 'quit'):
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
    parser.add_argument("-r", "--restore", action="store_true", help="Restore conversation continuing from previous.")
    parser.add_argument("-review", "--code_review", action="store_true", help="Apply code review system prompt to piped input.")
    parser.add_argument("text", nargs="*", help="Text to send to the AI model")
    args = parser.parse_args()

    global MODEL
    if args.model:
        MODEL = MODEL_4

    setup_api()
    conversation = [] # start with a blank conversation

    if args.restore:
        print(Fore.YELLOW + "Restoring previous conversation..." + Style.RESET_ALL)
        conversation = load_history() # only load history if interactive

    if args.c:
        handle_code_output(args)
        return

    stdin_data = None
    if check_stdin():
        stdin_data = read_stdin()

    prompt_args = concatenate_arguments(*args.text)

    if stdin_data or prompt_args:
        full_prompt = f"{prompt_args}\n\n{stdin_data}" if prompt_args and stdin_data else (prompt_args or stdin_data)
        messages = []
        if args.code_review and not conversation:
            messages.append({"role": "system", "content": CODE_REVIEW_SYSTEM_PROMPT})
            conversation.append({"role": "system", "content": CODE_REVIEW_SYSTEM_PROMPT}) # Add to history
        messages.append({"role": "user", "content": full_prompt})

        print(Fore.YELLOW + "\nAI: " + Style.RESET_ALL, end='')
        response = interact_with_gpt(messages=messages, stream=True)
        conversation.append({"role": "user", "content": full_prompt})
        conversation.append({"role": "assistant", "content": response})
        save_history(conversation)

        if not args.restore:
            return  # Exit after processing stdin and/or command line args

    if args.restore:
        if sys.stdin.isatty():
            handle_conversation(conversation, stream=True, code_review=args.code_review)
        else:
            print(Fore.RED + "No interactive terminal available." + Style.RESET_ALL)
        return

    print(Fore.YELLOW + f"Welcome to AI CLI. Type 'exit', 'quit', or '/exit' to end the conversation. Using model: {MODEL}" + Style.RESET_ALL)
    handle_conversation(conversation, stream=True)


if __name__ == "__main__":
    main()
