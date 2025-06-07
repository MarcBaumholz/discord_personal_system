# Plan Bot

A Discord bot that helps create organized plans from lists of items.

## Features

- Generates formatted plans with your provided items
- Organizes tasks into a timeline format
- Works in the todoliste channel

## Usage

Type `plan` followed by your items to generate a plan:

```
plan item1, item2, item3
```

Or list items on separate lines:

```
plan
item1
item2
item3
```

Use `!help_plan` to see usage instructions.

## Configuration

- TODOLISTE_CHANNEL_ID: 1361083732638957669

## Dependencies

- discord.py
- python-dotenv 