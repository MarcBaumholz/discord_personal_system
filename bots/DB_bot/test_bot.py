#!/usr/bin/env python3
"""
Test Script für S-Bahn Monitor Bot
Prüft Dependencies, Environment Variables und grundlegende Funktionalität
"""

import os
import sys
from pathlib import Path

def test_environment():
    """Testet Python Virtual Environment"""
    print("🔍 Testing Virtual Environment...")
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual Environment aktiv")
        print(f"   Python: {sys.executable}")
        print(f"   Prefix: {sys.prefix}")
    else:
        print("❌ Nicht in Virtual Environment!")
        print("   Führe aus: source db_env/bin/activate")
        return False
    
    return True

def test_dependencies():
    """Testet alle Required Dependencies"""
    print("\n🔍 Testing Dependencies...")
    
    required_packages = [
        'discord',
        'httpx', 
        'dotenv',
        'aiofiles'
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - nicht installiert!")
            all_ok = False
    
    if not all_ok:
        print("\n💡 Installiere fehlende Packages:")
        print("   pip install discord.py httpx python-dotenv aiofiles")
    
    return all_ok

def test_environment_variables():
    """Testet Environment Variables"""
    print("\n🔍 Testing Environment Variables...")
    
    # Load dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv()
        load_dotenv("../../../.env")  # Parent directory
        print("✅ dotenv loaded")
    except Exception as e:
        print(f"❌ dotenv loading failed: {e}")
        return False
    
    # Check required variables
    required_vars = {
        'DISCORD_TOKEN': 'Discord Bot Token',
        'DB_CLIENT_ID': 'Deutsche Bahn Client ID', 
        'DB_API_KEY': 'Deutsche Bahn API Key'
    }
    
    all_ok = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Don't show full token for security
            if 'TOKEN' in var or 'KEY' in var:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Nicht gesetzt! ({description})")
            all_ok = False
    
    # Check optional variables
    optional_vars = ['SCHWAIKHEIM_ID', 'FEUERSEE_ID', 'CACHE_TTL_MINUTES']
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"🔧 {var}: {value}")
    
    return all_ok

def test_file_structure():
    """Testet Datei- und Ordnerstruktur"""
    print("\n🔍 Testing File Structure...")
    
    required_files = [
        'sbahn_monitor.py',
        'requirements.txt',
        'env.example'
    ]
    
    required_dirs = [
        'api_logs',
        'db_env'
    ]
    
    all_ok = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - nicht gefunden!")
            all_ok = False
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - nicht gefunden!")
            all_ok = False
    
    return all_ok

def test_api_imports():
    """Testet ob Bot-Module importiert werden können"""
    print("\n🔍 Testing Bot Imports...")
    
    try:
        # Test core imports
        import discord
        from discord.ext import commands
        import httpx
        import aiofiles
        print("✅ Core imports erfolgreich")
        
        # Test bot file syntax
        import ast
        with open('sbahn_monitor.py', 'r') as f:
            source = f.read()
        ast.parse(source)
        print("✅ sbahn_monitor.py Syntax OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Import Error: {e}")
        return False

def show_next_steps():
    """Zeigt nächste Schritte"""
    print("\n" + "="*50)
    print("🚀 NÄCHSTE SCHRITTE")
    print("="*50)
    
    print("\n1. 🔑 Deutsche Bahn API Setup:")
    print("   → Gehe zu: https://developers.deutschebahn.com/db-api-marketplace")
    print("   → Registriere Account mit BahnID")
    print("   → Erstelle neue Anwendung")
    print("   → Abonniere RIS::Stations (Free Plan)")
    print("   → Abonniere RIS::Journeys (Free Plan)")
    print("   → Kopiere Client-ID und API-Key")
    
    print("\n2. 📝 Environment Configuration:")
    print("   → cp env.example .env")
    print("   → Trage DB_CLIENT_ID und DB_API_KEY ein")
    print("   → Prüfe DISCORD_TOKEN aus parent directory")
    
    print("\n3. 🚆 Bot testen:")
    print("   → python sbahn_monitor.py")
    print("   → Teste Discord Befehle: 1, 2, status, help")
    
    print("\n4. 📊 Monitoring:")
    print("   → Prüfe api_logs/ für API-Calls")
    print("   → Überwache Free-Plan Limits (1000/Tag)")

def main():
    """Haupttest-Funktion"""
    print("🧪 S-Bahn Monitor Bot - Test Suite")
    print("="*50)
    
    tests = [
        ("Virtual Environment", test_environment),
        ("Dependencies", test_dependencies),
        ("Environment Variables", test_environment_variables),
        ("File Structure", test_file_structure),
        ("Bot Imports", test_api_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Gesamt: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests bestanden! Bot ist bereit.")
    else:
        print("⚠️  Einige Tests fehlgeschlagen. Prüfe Konfiguration.")
    
    show_next_steps()

if __name__ == "__main__":
    main() 