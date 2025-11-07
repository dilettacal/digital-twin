"""Prompt loading and caching utilities."""
import json
from pathlib import Path
from typing import Dict, List
from functools import lru_cache

# Get the prompts directory path (backend/data/prompts)
PROMPTS_DIR = Path(__file__).parent.parent.parent / "data" / "prompts"


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """
    Load the system prompt template from file.
    Cached for performance.
    """
    prompt_file = PROMPTS_DIR / "system_prompt.txt"
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()


@lru_cache(maxsize=1)
def load_critical_rules() -> List[str]:
    """
    Load critical rules from file.
    Returns a list of rules, one per line (ignoring empty lines).
    Cached for performance.
    """
    rules_file = PROMPTS_DIR / "critical_rules.txt"
    with open(rules_file, "r", encoding="utf-8") as f:
        rules = [line.strip() for line in f.readlines() if line.strip()]
    return rules


@lru_cache(maxsize=1)
def load_proficiency_levels() -> Dict[int, str]:
    """
    Load proficiency level mappings from JSON file.
    Cached for performance.
    """
    levels_file = PROMPTS_DIR / "proficiency_levels.json"
    with open(levels_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Convert string keys to integers
    return {int(k): v for k, v in data.items()}


def format_critical_rules(rules: List[str]) -> str:
    """Format critical rules as numbered list."""
    return "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(rules)])


def clear_prompt_cache():
    """
    Clear the prompt cache.
    Useful for reloading prompts after changes during development.
    """
    load_system_prompt.cache_clear()
    load_critical_rules.cache_clear()
    load_proficiency_levels.cache_clear()

