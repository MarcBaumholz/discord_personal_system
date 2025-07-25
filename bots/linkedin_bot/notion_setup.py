#!/usr/bin/env python3
"""
Notion Database Setup Utility
Creates the LinkedIn Contacts database in Notion with proper schema
"""

import os
from notion_client import Client as NotionClient
from dotenv import load_dotenv
import json

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# Topic categories for the select field
TOPIC_CATEGORIES = [
    "Artificial Intelligence & Machine Learning",
    "Software Development & Engineering", 
    "Data Science & Analytics",
    "Product Management",
    "Digital Marketing & Growth",
    "Finance & Investment",
    "Entrepreneurship & Startups",
    "Consulting & Strategy",
    "Sales & Business Development",
    "Human Resources & Recruiting",
    "Design & UX/UI",
    "Content Creation & Media",
    "Healthcare & Life Sciences",
    "Education & Training",
    "Other"
]

def create_linkedin_contacts_database(parent_page_id: str):
    """Create the LinkedIn Contacts database in Notion"""
    
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN not found in environment variables")
        return None
    
    notion = NotionClient(auth=NOTION_TOKEN)
    
    # Database properties schema
    database_properties = {
        "Name": {
            "title": {}
        },
        "Position": {
            "rich_text": {}
        },
        "Company": {
            "rich_text": {}
        },
        "Profile URL": {
            "url": {}
        },
        "Email": {
            "email": {}
        },
        "Follower Count": {
            "number": {
                "format": "number"
            }
        },
        "Topic Category": {
            "select": {
                "options": [
                    {"name": category, "color": "default"} 
                    for category in TOPIC_CATEGORIES
                ]
            }
        },
        "Importance Score": {
            "number": {
                "format": "number"
            }
        },
        "Last Interaction": {
            "date": {}
        },
        "Notes": {
            "rich_text": {}
        },
        "Top 10 Flag": {
            "checkbox": {}
        },
        "Created Date": {
            "created_time": {}
        },
        "Last Updated": {
            "last_edited_time": {}
        }
    }
    
    try:
        # Create the database
        response = notion.databases.create(
            parent={
                "type": "page_id",
                "page_id": parent_page_id
            },
            title=[
                {
                    "type": "text",
                    "text": {
                        "content": "LinkedIn Network Analysis"
                    }
                }
            ],
            properties=database_properties,
            icon={
                "type": "emoji",
                "emoji": "🔗"
            }
        )
        
        database_id = response['id']
        print(f"✅ Successfully created LinkedIn Contacts database!")
        print(f"📊 Database ID: {database_id}")
        print(f"🔗 Database URL: {response['url']}")
        
        # Add the database ID to environment variables instruction
        print("\n📝 Next Steps:")
        print("1. Add this to your .env file:")
        print(f"   LINKEDIN_CONTACTS_DB_ID={database_id}")
        print("2. Share the database with your Notion integration")
        print("3. Run the LinkedIn bot with !analyze_network command")
        
        return database_id
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return None

def verify_database_access(database_id: str):
    """Verify that we can access the database"""
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN not found")
        return False
    
    notion = NotionClient(auth=NOTION_TOKEN)
    
    try:
        response = notion.databases.retrieve(database_id=database_id)
        print(f"✅ Database access verified: {response['title'][0]['text']['content']}")
        return True
    except Exception as e:
        print(f"❌ Cannot access database: {e}")
        return False

def add_sample_contact(database_id: str):
    """Add a sample contact to test the database"""
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN not found")
        return False
    
    notion = NotionClient(auth=NOTION_TOKEN)
    
    sample_contact = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": "Max Mustermann"
                    }
                }
            ]
        },
        "Position": {
            "rich_text": [
                {
                    "text": {
                        "content": "Senior Software Engineer"
                    }
                }
            ]
        },
        "Company": {
            "rich_text": [
                {
                    "text": {
                        "content": "Tech Startup GmbH"
                    }
                }
            ]
        },
        "Email": {
            "email": "max.mustermann@example.com"
        },
        "Follower Count": {
            "number": 1500
        },
        "Topic Category": {
            "select": {
                "name": "Software Development & Engineering"
            }
        },
        "Importance Score": {
            "number": 8
        },
        "Notes": {
            "rich_text": [
                {
                    "text": {
                        "content": "Experienced developer with strong network in Berlin tech scene. Active in open source projects."
                    }
                }
            ]
        },
        "Top 10 Flag": {
            "checkbox": True
        }
    }
    
    try:
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties=sample_contact
        )
        print(f"✅ Sample contact added successfully!")
        print(f"🔗 Contact URL: {response['url']}")
        return True
    except Exception as e:
        print(f"❌ Error adding sample contact: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    print("🔗 LinkedIn Contacts Database Setup")
    print("=====================================\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python notion_setup.py create <parent_page_id>")
        print("  python notion_setup.py verify <database_id>")
        print("  python notion_setup.py sample <database_id>")
        print("\nTo get parent_page_id:")
        print("1. Create a new page in Notion")
        print("2. Copy the page ID from the URL")
        print("   Example: https://notion.so/MyPage-abc123... → abc123 is the page ID")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) != 3:
            print("❌ Please provide parent_page_id")
            print("Usage: python notion_setup.py create <parent_page_id>")
            sys.exit(1)
        
        parent_page_id = sys.argv[2]
        create_linkedin_contacts_database(parent_page_id)
    
    elif command == "verify":
        if len(sys.argv) != 3:
            print("❌ Please provide database_id")
            print("Usage: python notion_setup.py verify <database_id>")
            sys.exit(1)
        
        database_id = sys.argv[2]
        verify_database_access(database_id)
    
    elif command == "sample":
        if len(sys.argv) != 3:
            print("❌ Please provide database_id")
            print("Usage: python notion_setup.py sample <database_id>")
            sys.exit(1)
        
        database_id = sys.argv[2]
        add_sample_contact(database_id)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: create, verify, sample")
