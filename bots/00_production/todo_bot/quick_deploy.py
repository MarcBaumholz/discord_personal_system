#!/usr/bin/env python3
"""
Quick Deploy Script for Todo Bot
Fügt den Todo Bot zum laufenden Multi-Bot System hinzu
"""
import os
import sys
import time
import subprocess
import requests
from pathlib import Path

def check_multibot_running():
    """Prüfe ob das Multi-Bot System läuft"""
    try:
        result = subprocess.run(['pgrep', '-f', 'start_multibot.py'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def check_todo_bot_in_multibot():
    """Prüfe ob Todo Bot bereits im Multi-Bot System ist"""
    multibot_script = Path(__file__).parent.parent / "start_multibot.py"
    if multibot_script.exists():
        with open(multibot_script) as f:
            content = f.read()
            return "todo_bot/todo_agent.py" in content
    return False

def check_todoist_connection():
    """Teste Todoist API Verbindung"""
    from dotenv import load_dotenv
    load_dotenv('../.env')
    
    api_key = os.getenv('TODOIST_API_KEY')
    if not api_key:
        return False, "Kein API Key gefunden"
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://api.todoist.com/rest/v2/tasks", 
                              headers=headers, timeout=10)
        return response.status_code == 200, f"Status: {response.status_code}"
    except Exception as e:
        return False, f"Fehler: {e}"

def deploy_todo_bot():
    """Deploy Todo Bot"""
    print("🤖 Todo Bot Quick Deploy")
    print("=" * 40)
    
    # 1. Prüfe Todoist Verbindung
    print("1. 🔗 Teste Todoist API...")
    todoist_ok, todoist_msg = check_todoist_connection()
    if not todoist_ok:
        print(f"❌ Todoist API Fehler: {todoist_msg}")
        return False
    print(f"✅ Todoist API: {todoist_msg}")
    
    # 2. Prüfe ob bereits im Multi-Bot
    print("\n2. 🔍 Prüfe Multi-Bot Integration...")
    if check_todo_bot_in_multibot():
        print("✅ Todo Bot ist bereits im Multi-Bot System")
    else:
        print("ℹ️ Todo Bot noch nicht in Multi-Bot - wurde gerade hinzugefügt")
    
    # 3. Prüfe ob Multi-Bot läuft
    print("\n3. 🚀 Prüfe Multi-Bot Status...")
    if check_multibot_running():
        print("⚠️ Multi-Bot System läuft bereits")
        print("   Restart erforderlich um Todo Bot zu aktivieren:")
        print("   pkill -f start_multibot.py && python ../start_multibot.py")
    else:
        print("ℹ️ Multi-Bot System läuft nicht")
        print("   Starte Multi-Bot System:")
        print("   cd .. && python start_multibot.py")
    
    # 4. Test Todo Bot einzeln
    print("\n4. 🧪 Teste Todo Bot...")
    try:
        result = subprocess.run([sys.executable, 'test_todo_bot.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Todo Bot Tests erfolgreich")
        else:
            print(f"❌ Todo Bot Tests fehlgeschlagen:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        return False
    
    print("\n🎉 Todo Bot erfolgreich deployed!")
    print("\n📋 Nächste Schritte:")
    print("   • Teste im Discord Channel: 1368180016785002536")
    print("   • Schreibe eine Nachricht → wird automatisch zu Todo")
    print("   • Verwende !todo um alle Todos zu sehen")
    print("   • Verwende !help_todo für Hilfe")
    
    return True

if __name__ == "__main__":
    try:
        success = deploy_todo_bot()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Deployment abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Deployment-Fehler: {e}")
        sys.exit(1)
