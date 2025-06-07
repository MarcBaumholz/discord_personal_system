# Finance Bot

A Discord bot that helps track expenses, provides budget alerts, and connects to German bank accounts using FinTS.

## Features

- Connect to German bank accounts (Volksbank, MLP, DKB) using FinTS/HBCI protocol
- Access PayPal transaction data
- Track expenses across multiple accounts
- Set budget limits and receive alerts
- Generate spending reports

## Implementation Plan

1. **Basic Bot Structure**
   - Create Discord bot framework
   - Implement command handlers
   - Setup environment configuration

2. **Bank Data Integration**
   - Implement python-fints for German banks
   - Create PayPal API integration
   - Build transaction fetching functionality

3. **Budget Management**
   - Create budget setting and storage
   - Implement category detection for transactions
   - Build budget comparison logic

4. **Notification System**
   - Design alert thresholds
   - Implement Discord notification methods
   - Create scheduled checks

5. **Security**
   - Implement secure credential storage
   - Add user authentication
   - Ensure data privacy

## Dependencies

- discord.py
- python-dotenv
- python-fints
- requests (for PayPal API)
- SQLite (for local data storage)

## Configuration

The bot requires the following environment variables:
- DISCORD_TOKEN
- FINTS_URL (URL for your bank's FinTS endpoint)
- FINTS_BLZBANK_BLZ (Bank code)
- FINTS_USERNAME
- FINTS_PIN (encrypted) 