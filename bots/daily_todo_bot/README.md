# Daily Todo Bot

A Discord bot that manages recurring daily todos with persistent state tracking.

## Features

- Displays a list of daily todos
- Allows marking tasks as complete with number reactions
- Saves completion status for the day
- Automatically resets todos for a new day
- Stores completed todos in a JSON file

## Usage

Simply type `:white_check_mark:` or `✅` in the haushaltsplan channel to see your daily todos.

To mark a todo as complete:
1. React with the number of the todo
2. React again to toggle it back to incomplete

Use `!help_todo` to view help information.

## Configuration

- HAUSHALTSPLAN_CHANNEL_ID: 1361083769427202291
- Default todos are defined in the script
- Completed todos are saved in `completed_todos.json`

## Dependencies

- discord.py
- python-dotenv
- json 