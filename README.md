# Quick Start Guide

## Step 1: Clone the Repository
Start by cloning our repository to your local system using the git command:

```sh
git clone https://github.com/ljsimpkin/chat-gpt-cli-tool.git
```

## Step 2: Install Dependencies
Navigate to your project's directory and install the necessary dependencies using pip:

```sh
cd YourProject
python3 -m pip install -r requirements.txt
```

## Step 3: Set Your OpenAI API Key
Before running the script, you should set your `OPENAI_API_KEY` in your environment variables. Below are the instructions for Unix/Linux systems and Windows respectively.

### Unix/Linux
On Unix/Linux you can add the api key to your environment variables using the command below:
```sh
export OPENAI_API_KEY=your-api-key
```

### Windows
On Windows, environment variables can be set through the command prompt with the setx command:
```sh
setx OPENAI_API_KEY "your-api-key"
```

Remember to replace `your-api-key` with your actual OpenAI API Key.

## Step 4: Run the Script
Now, you can run your python script. Instead of using pip, we are using python3 script here:

```sh
python3 your_script.py
```
This should start the execution of the script.

Congratulations! You are all set.

<span style="color:blue">*__NOTE__:</span> For these changes to take effect, you might need to close and reopen your command line session or reboot your machine.

__IMPORTANT:__ Please make sure to keep your `OPENAI_API_KEY` secure and do not commit it in your code or upload it to GitHub. 

Enjoy using our project!

# Todo
[] Create a -c flag that will instruct the ai to only output code