from openai import OpenAI
import os
import argparse
from colorama import Fore, Style
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input import DummyInput
from prompt_toolkit.input.defaults import create_input
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.output.defaults import create_output
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


def apply_code_review_prompt(conversation, messages, enabled):
    """Ensure the code review system prompt is present when requested."""
    if not enabled:
        return

    def ensure_prompt(target):
        if target is None:
            return
        for message in target:
            if message.get("role") == "system" and message.get("content") == CODE_REVIEW_SYSTEM_PROMPT:
                return
        target.insert(0, {"role": "system", "content": CODE_REVIEW_SYSTEM_PROMPT})

    ensure_prompt(conversation)
    ensure_prompt(messages)


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


def process_single_prompt(
    prompt_text,
    *,
    stream,
    conversation=None,
    code_review=False,
    system_prompt=None,
    copy_result=False,
    include_history=False,
    save_history_flag=True,
    announce_prefix="\nAI: "
):
    """Prepare and dispatch a single prompt to the model, updating history as needed."""
    messages = []
    if include_history and conversation:
        messages = list(conversation)
    else:
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
    apply_code_review_prompt(conversation, messages, code_review)
    messages.append({"role": "user", "content": prompt_text})

    if stream:
        if announce_prefix is not None:
            print(Fore.YELLOW + announce_prefix + Style.RESET_ALL, end='')
        response = interact_with_gpt(messages=messages, stream=True)
    else:
        response = interact_with_gpt(messages=messages, stream=False)
        if announce_prefix is not None:
            print(Fore.YELLOW + announce_prefix + Style.RESET_ALL)
        print(Fore.YELLOW + response + Style.RESET_ALL)

    if conversation is not None:
        conversation.append({"role": "user", "content": prompt_text})
        conversation.append({"role": "assistant", "content": response})
        if save_history_flag:
            save_history(conversation)

    if copy_result:
        copy_to_clipboard(response)

    return response


def handle_conversation(conversation, stream=False, code_review=False, prompt_session=None):
    """Handles the conversation with the AI model."""
    apply_code_review_prompt(conversation, None, code_review)

    if prompt_session is None:
        prompt_session = PromptSession(history=InMemoryHistory())

    while True:
        try:
            user_input = prompt_session.prompt("You: ")
        except (EOFError, KeyboardInterrupt):
            print("Exiting conversation.")
            break

        normalized_input = user_input.strip().lower()
        if normalized_input in ('/exit', 'exit', 'quit'):
            print("Exiting conversation.")
            break

        process_single_prompt(
            user_input,
            stream=stream,
            conversation=conversation,
            code_review=code_review,
            include_history=True
        )


def build_prompt_session():
    """Create a prompt session that prefers the active terminal when available."""
    input_device = create_input(always_prefer_tty=True)
    output_device = create_output(always_prefer_tty=True)

    if isinstance(input_device, DummyInput) or isinstance(output_device, DummyOutput):
        return None

    return PromptSession(history=InMemoryHistory(), input=input_device, output=output_device)


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
        prompt_args = concatenate_arguments(*args.c)
        process_single_prompt(
            prompt_args,
            stream=False,
            system_prompt=CODE_FLAG,
            copy_result=True,
            announce_prefix=None,
            save_history_flag=False
        )
        return

    stdin_data = None
    if check_stdin():
        stdin_data = read_stdin()

    prompt_args = concatenate_arguments(*args.text)

    piped_request_handled = False

    if stdin_data or prompt_args:
        full_prompt = f"{prompt_args}\n\n{stdin_data}" if prompt_args and stdin_data else (prompt_args or stdin_data)
        process_single_prompt(
            full_prompt,
            stream=True,
            conversation=conversation,
            code_review=args.code_review,
            include_history=False
        )

        piped_request_handled = True

    prompt_session = build_prompt_session()

    if args.restore:
        if prompt_session is not None:
            handle_conversation(conversation, stream=True, code_review=args.code_review, prompt_session=prompt_session)
        else:
            print(Fore.RED + "No interactive terminal available." + Style.RESET_ALL)
        return

    if prompt_session is None:
        if piped_request_handled:
            print(Fore.RED + "Interactive mode unavailable after processing piped input." + Style.RESET_ALL)
        else:
            print(Fore.RED + "No interactive terminal available." + Style.RESET_ALL)
        return

    if piped_request_handled:
        print(Fore.YELLOW + "Switching to interactive mode. Type 'exit', 'quit', or '/exit' to finish." + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + f"Welcome to AI CLI. Type 'exit', 'quit', or '/exit' to end the conversation. Using model: {MODEL}" + Style.RESET_ALL)

    handle_conversation(conversation, stream=True, prompt_session=prompt_session)


if __name__ == "__main__":
    main()
