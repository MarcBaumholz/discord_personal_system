#!/usr/bin/env python3
"""
Simple health check for Docker container
"""
import sys
import os
import requests

def main():
    """Simple health check"""
    try:
        # Check if we have required env vars
        if not os.getenv('TODOIST_API_KEY'):
            sys.exit(1)
        
        if not os.getenv('DISCORD_TOKEN'):
            sys.exit(1)
            
        # Quick API check
        api_key = os.getenv('TODOIST_API_KEY')
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(
            "https://api.todoist.com/rest/v2/tasks", 
            headers=headers, 
            timeout=5
        )
        
        if response.status_code == 200:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except Exception:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
