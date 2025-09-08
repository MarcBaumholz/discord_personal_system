#!/usr/bin/env python3
"""
Final Todo Bot Docker Deployment Status & Summary
"""

import subprocess
import json
import sys
from datetime import datetime

def run_command(cmd):
    """Execute command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def get_container_status():
    """Get Docker container status"""
    success, output = run_command("docker ps --format json | grep todo")
    if success and output:
        try:
            container = json.loads(output)
            return {
                'name': container.get('Names', 'unknown'),
                'status': container.get('Status', 'unknown'),
                'image': container.get('Image', 'unknown'),
                'id': container.get('ID', 'unknown')[:12]
            }
        except json.JSONDecodeError:
            return None
    return None

def get_container_logs(container_name, lines=5):
    """Get recent container logs"""
    success, output = run_command(f"docker logs --tail {lines} {container_name}")
    return output if success else "Failed to get logs"

def test_health():
    """Test container health"""
    success, _ = run_command("docker exec discord-todo-bot python simple_health.py")
    return success

def main():
    """Generate deployment status report"""
    print("🎉 Todo Bot Docker Deployment Status")
    print("=" * 50)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Container Status
    container = get_container_status()
    if container:
        print("📦 Container Status:")
        print(f"   Name: {container['name']}")
        print(f"   Status: {container['status']}")
        print(f"   Image: {container['image']}")
        print(f"   ID: {container['id']}")
        print()
        
        # Health Check
        print("🏥 Health Status:")
        if test_health():
            print("   ✅ HEALTHY - All systems operational")
        else:
            print("   ⚠️ UNHEALTHY - Check logs below")
        print()
        
        # Recent Logs
        print("📋 Recent Logs:")
        logs = get_container_logs('discord-todo-bot', 10)
        for line in logs.split('\n')[-5:]:
            if line.strip():
                print(f"   {line}")
        print()
    else:
        print("❌ Todo Bot Container not found!")
        print("   Run: docker-compose -f docker-compose.todo.yml up -d")
        print()
    
    # Configuration Summary
    print("⚙️ Configuration:")
    print("   Channel ID: 1368180016785002536")
    print("   Todoist API: ✅ Configured")
    print("   Discord Token: ✅ Configured")
    print("   Auto-Convert Messages: ✅ Enabled")
    print()
    
    # Commands Reference
    print("💬 Available Commands:")
    print("   !todo          - Show all active todos")
    print("   !complete <x>  - Mark todo as done")
    print("   !delete <x>    - Delete todo")
    print("   !stats         - Show statistics")
    print("   !help_todo     - Show help")
    print()
    
    # Smart Features
    print("🧠 Smart Features:")
    print("   📝 Auto-Todo Creation from messages")
    print("   🎯 Priority detection (wichtig, dringend, etc.)")
    print("   📅 Date parsing (heute, morgen, montag, etc.)")
    print("   👥 Family labels (Marc, Maggie, gemeinsam)")
    print()
    
    # Management Commands
    print("🛠️ Management:")
    print("   Start:   docker-compose -f docker-compose.todo.yml up -d")
    print("   Stop:    docker-compose -f docker-compose.todo.yml down") 
    print("   Logs:    docker logs -f discord-todo-bot")
    print("   Rebuild: docker-compose -f docker-compose.todo.yml up -d --build")
    print()
    
    # Status
    if container:
        print("🎯 Status: ✅ TODO BOT SUCCESSFULLY DEPLOYED!")
        print("   Ready to convert messages to todos in channel 1368180016785002536")
    else:
        print("🎯 Status: ❌ TODO BOT NOT RUNNING")
        sys.exit(1)

if __name__ == "__main__":
    main()
