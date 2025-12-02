# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool for interacting with OpenAI's GPT models (gpt-4o-mini and gpt-4o). The entire application is contained in `main.py` with no sub-modules or packages.

## Environment Setup

**Virtual Environment:** This project uses a Python virtual environment located in `venv/`.

Install dependencies:
```sh
/home/liam/code/chat-gpt-cli-tool/venv/bin/pip install -r requirements.txt
```

Run the application:
```sh
/home/liam/code/chat-gpt-cli-tool/venv/bin/python main.py
```

**Required Environment Variable:** `OPENAI_API_KEY` must be set for the application to function.

## Application Architecture

### Single-File Design
The entire application lives in `main.py` (~200 lines). There is no module structure or separation of concerns into multiple files.

### Key Components

**Global Configuration** (lines 11-20):
- `openai_client`: Global OpenAI client instance
- Model selection: `MODEL` (gpt-4o-mini default) and `MODEL_4` (gpt-4o)
- `CODE_FLAG`: System prompt for code-only generation mode
- `CODE_REVIEW_SYSTEM_PROMPT`: Detailed system prompt for code review mode

**Conversation History** (lines 91-103):
- Persisted to `.ai_cli_history.json` in JSON format
- Stores full conversation array with role/content objects
- Loaded/saved via `load_history()` and `save_history()`

**Interaction Modes** (main function, lines 142-198):
The application has multiple execution paths controlled by CLI arguments:

1. **Code Output Mode** (`-c` flag): Generates raw code, copies to clipboard, exits
2. **Piped Input Mode** (stdin detection): Processes piped content with optional code review, can chain into interactive mode with `-r`
3. **Restore Mode** (`-r` flag): Loads history and enters interactive conversation
4. **Interactive Mode** (default): Streaming conversation loop with prompt toolkit

**Response Handling**:
- `interact_with_gpt()`: Main API call wrapper, delegates to streaming if requested
- `interact_with_gpt_stream()`: Handles streaming responses with colored output via colorama
- All interactive modes use streaming; code output mode does not

### CLI Argument Logic

The argument parser accepts multiple flag combinations, executed in this order:
1. Model toggle (`-m`) sets global MODEL
2. Code output (`-c`) takes priority, exits after generation
3. Stdin/args processed if present, with optional system prompt injection for code review
4. Restore mode (`-r`) loads history; if combined with stdin/args, continues to interactive mode
5. Default: enters interactive conversation

### Special Commands
- `/exit`: Exit interactive mode (handled in `handle_conversation()`)

## Common Issues

**OpenAI Library Version**: The `requirements.txt` may specify an outdated version of `openai`. If you encounter `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`, upgrade openai:
```sh
/home/liam/code/chat-gpt-cli-tool/venv/bin/pip install --upgrade openai
```

**Clipboard Support**: Uses `pyperclip` which may require additional system dependencies on some platforms.
