import os
import random
from pathlib import Path
from typing import List, Tuple, Optional
import csv

DATA_DIR = Path(__file__).parent / 'data' / 'Private & Shared'


def get_all_files() -> List[Path]:
    """Recursively get all .md and .csv files in the data directory."""
    return [f for f in DATA_DIR.rglob('*') if f.suffix in ['.md', '.csv']]


def extract_md_learning(file_path: Path) -> Tuple[str, str, Optional[str]]:
    """Extract title, main content, and action steps from a markdown file."""
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    title = lines[0].strip('#').strip() if lines and lines[0].startswith('#') else file_path.stem
    content = []
    action_steps = []
    in_action = False
    for line in lines[1:]:
        if 'step by step' in line.lower() or 'how you apply' in line.lower():
            in_action = True
            continue
        if in_action:
            if line.strip() == '' or line.startswith('#'):
                in_action = False
                continue
            action_steps.append(line.strip())
        else:
            content.append(line.strip())
    main_content = '\n'.join([l for l in content if l])
    actions = '\n'.join([l for l in action_steps if l]) if action_steps else None
    return title, main_content, actions


def extract_csv_learning(file_path: Path) -> Tuple[str, str, Optional[str]]:
    """Randomly select a row from a CSV and format as a learning."""
    with open(file_path, encoding='utf-8') as f:
        reader = list(csv.reader(f))
    if len(reader) < 2:
        return file_path.stem, '', None
    header = reader[0]
    row = random.choice(reader[1:])
    content = '\n'.join(f'{h}: {v}' for h, v in zip(header, row))
    return file_path.stem, content, None


def get_random_learning() -> Tuple[str, str, Optional[str]]:
    """Get a random learning from all available files."""
    files = get_all_files()
    if not files:
        return 'No Learnings Found', '', None
    file_path = random.choice(files)
    if file_path.suffix == '.md':
        return extract_md_learning(file_path)
    elif file_path.suffix == '.csv':
        return extract_csv_learning(file_path)
    else:
        return file_path.stem, '', None 