#!/usr/bin/env python3
"""
Stop All Bots - Emergency stop script
Kills all Python processes that might be running bots
"""

import subprocess
import os
import sys

def stop_all_python_processes():
    """Stop all Python processes (be careful!)"""
    try:
        # Get all Python processes
        result = subprocess.run(['pgrep', '-f', 'python.*bot'], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"🔍 Found {len(pids)} bot processes to stop:")
            
            for pid in pids:
                try:
                    # Get process info
                    cmd_result = subprocess.run(['ps', '-p', pid, '-o', 'comm='], capture_output=True, text=True)
                    process_name = cmd_result.stdout.strip() if cmd_result.returncode == 0 else "unknown"
                    
                    print(f"  🔄 Stopping PID {pid} ({process_name})")
                    
                    # Try graceful termination first
                    subprocess.run(['kill', '-TERM', pid], check=False)
                    
                except Exception as e:
                    print(f"  ❌ Error stopping PID {pid}: {e}")
            
            # Wait a moment for graceful shutdown
            import time
            time.sleep(3)
            
            # Force kill any remaining processes
            result = subprocess.run(['pgrep', '-f', 'python.*bot'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                remaining_pids = result.stdout.strip().split('\n')
                print(f"⚡ Force killing {len(remaining_pids)} remaining processes...")
                
                for pid in remaining_pids:
                    try:
                        subprocess.run(['kill', '-KILL', pid], check=False)
                        print(f"  💀 Force killed PID {pid}")
                    except Exception as e:
                        print(f"  ❌ Error force killing PID {pid}: {e}")
            
            print("✅ All bot processes stopped")
        else:
            print("ℹ️  No bot processes found running")
            
    except Exception as e:
        print(f"❌ Error stopping processes: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🛑 EMERGENCY STOP - Stopping all bot processes")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("⚠️  FORCE MODE: Will kill ALL Python processes!")
        stop_all_python_processes()
    else:
        print("🔍 Stopping bot-related Python processes only...")
        stop_all_python_processes()
    
    print("=" * 50)
    print("✅ Stop script completed")
