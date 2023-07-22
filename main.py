import argparse
import openai
import os

def setup_openai():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environmental variable.")
    openai.api_key = api_key

def interact_with_gpt3(prompt, max_tokens=50):
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()

def main():
    setup_openai()

    print("Welcome to ChatGPT CLI. Type 'exit' to end the conversation.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        response = interact_with_gpt3(prompt=user_input)
        print("ChatGPT:", response)

if __name__ == "__main__":
    main()
