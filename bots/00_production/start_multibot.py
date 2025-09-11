#!/usr/bin/env python3
"""Start the 5 selected bots in parallel:
- Money Bot
- Calories Bot
- Allgemeine Wohl Bot
- Preisvergleich Bot
- Erinnerungen Bot

Each bot runs in its own subprocess so if one crashes others continue.
We also log stdout lines with a prefix for easy grepping.
"""
import subprocess, sys, time, os, signal, threading
from datetime import datetime

BOT_SCRIPTS = [
    # name, relative path
    ("money", "bots/00_production/money_bot-1/bot.py"),
    ("calories", "bots/00_production/Calories_bot/calories_bot.py"),
    ("allgemeine", "bots/00_production/allgemeineWohl/allgemeine_wohl_bot.py"),
    ("preisvergleich", "bots/00_production/preisvergleich_bot/preisvergleich_bot.py"),
    ("erinnerungen", "bots/00_production/Erinnerungen_bot/erinnerungen_bot.py"),
    ("todo", "bots/00_production/todo_bot/todo_agent.py"),
    ("log", "bots/00_production/log_bot/log_bot.py"),
    ("whoop", "bots/00_production/whoop_bot/bot.py"),
]

processes = {}
stop_flag = False

LOG_DIR = os.path.join("logs", "multibot")
os.makedirs(LOG_DIR, exist_ok=True)

ENV_FILE = os.path.join("discord", ".env") if os.path.exists("discord/.env") else ".env"
if os.path.exists(ENV_FILE):
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)


def start_bot(name, path):
    env = os.environ.copy()
    env['PYTHONPATH'] = '/app'
    return subprocess.Popen([sys.executable, path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)


def reader_thread(name, proc):
    log_path = os.path.join(LOG_DIR, f"{name}.log")
    with open(log_path, 'a', encoding='utf-8') as f:
        for line in proc.stdout:
            ts = datetime.utcnow().isoformat()
            tagged = f"[{ts}][{name}] {line.rstrip()}"
            print(tagged)
            f.write(tagged + "\n")
    print(f"[{name}] stream ended")


def supervisor():
    global stop_flag
    while not stop_flag:
        for name, meta in list(processes.items()):
            proc = meta['proc']
            if proc.poll() is not None:
                print(f"⚠️ Bot '{name}' exited with code {proc.returncode}; restarting in 5s")
                time.sleep(5)
                new_proc = start_bot(name, meta['path'])
                processes[name]['proc'] = new_proc
                t = threading.Thread(target=reader_thread, args=(name, new_proc), daemon=True)
                t.start()
        time.sleep(10)


def shutdown(signum=None, frame=None):
    global stop_flag
    stop_flag = True
    print("Received shutdown signal, terminating bots...")
    for name, meta in processes.items():
        proc = meta['proc']
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
    sys.exit(0)


def main():
    # Start all bots
    for name, path in BOT_SCRIPTS:
        if not os.path.exists(path):
            print(f"❌ Missing bot script: {path}")
            continue
        proc = start_bot(name, path)
        processes[name] = {"proc": proc, "path": path}
        t = threading.Thread(target=reader_thread, args=(name, proc), daemon=True)
        t.start()
        time.sleep(1)  # small stagger

    # Supervisor thread
    threading.Thread(target=supervisor, daemon=True).start()

    # Signal handlers
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Keep alive
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
