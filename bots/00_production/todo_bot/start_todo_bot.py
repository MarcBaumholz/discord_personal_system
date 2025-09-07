#!/usr/bin/env python3
"""
Standalone starter for Todo Bot
Use this to run only the Todo Bot for testing
"""
import os
import sys

# Set up path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from todo_agent import main

if __name__ == "__main__":
    print("🤖 Starting Todo Bot...")
    main()
