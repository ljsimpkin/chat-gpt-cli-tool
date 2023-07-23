import openai
import os
import sys
import argparse

# MODEL="gpt-3.5-turbo"
MODEL="gpt-4-0613"

def concatenate_arguments(*args):
    return ' '.join(map(str, args))

def setup_openai():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environmental variable.")
    openai.api_key = api_key

def interact_with_gpt(prompt, max_tokens=50):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()

def main():
    setup_openai()

    arguments = sys.argv[1:]
    prompt_args = concatenate_arguments(*arguments)

    if prompt_args:
        response = interact_with_gpt(prompt=prompt_args)
        return print(response)
    
    print("Welcome to ChatGPT CLI. Type 'exit' to end the conversation.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        response = interact_with_gpt(prompt=user_input)
        print("ChatGPT:", response)

if __name__ == "__main__":
    main()
