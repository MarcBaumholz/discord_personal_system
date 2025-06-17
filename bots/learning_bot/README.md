# Learning Bot

A Discord bot that implements a Retrieval-Augmented Generation (RAG) system to learn from documents and answer questions about them.

## Features

- Document processing (PDF and DOCX support)
- Vector-based document storage and retrieval
- Question answering using LLM
- Discord integration with user-friendly commands

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- OpenRouter API Key

## Setup

1. Clone the repository and navigate to the bot directory:
   ```bash
   cd discord/bots/learning_bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your credentials:
   ```
   DISCORD_TOKEN=your_discord_token_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## Usage

1. Start the bot:
   ```bash
   python bot.py
   ```

2. Available Commands:
   - `!ping` - Check if the bot is responsive
   - `!help` - Display help message
   - `!learn` - Upload a document for learning (PDF or DOCX)
   - `!ask <question>` - Ask questions about the learned content
   - `!clear` - Clear all learned content

## How to Use

1. Upload a document:
   - Use the `!learn` command with a PDF or DOCX file attachment
   - The bot will process and store the document

2. Ask questions:
   - Use the `!ask` command followed by your question
   - The bot will search the stored documents and generate an answer

3. Clear content:
   - Use the `!clear` command to remove all stored documents
   - Start fresh with new documents

## Project Structure

- `bot.py` - Main bot file with Discord integration
- `document_processor.py` - Document loading and processing
- `vector_store.py` - Vector storage and retrieval
- `llm_service.py` - LLM integration for response generation
- `requirements.txt` - Project dependencies
- `CHANGES.md` - Development progress and changes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 