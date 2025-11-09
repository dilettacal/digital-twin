"""Prompt loading and caching utilities."""
import json
from pathlib import Path
from typing import Dict, List, Any
from functools import lru_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


def _log_cache_hit(loader_name: str) -> None:
    logger.debug("prompt_loader_cache_hit", loader=loader_name)


def _log_cache_miss(loader_name: str, path: Path) -> None:
    logger.info("prompt_loader_load", loader=loader_name, path=str(path))


# Get the prompts directory path (backend/data/prompts)
PROMPTS_DIR = Path(__file__).parent.parent.parent / "data" / "prompts"


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """
    Load the system prompt template from file.
    Cached for performance.
    """
    prompt_file = PROMPTS_DIR / "system_prompt.txt"
    _log_cache_miss("load_system_prompt", prompt_file)
    with open(prompt_file, "r", encoding="utf-8") as f:
        data = f.read()
    _log_cache_hit("load_system_prompt")
    return data


@lru_cache(maxsize=1)
def load_critical_rules() -> List[str]:
    """
    Load critical rules from file.
    Returns a list of rules, one per line (ignoring empty lines).
    Cached for performance.
    """
    rules_file = PROMPTS_DIR / "critical_rules.txt"
    _log_cache_miss("load_critical_rules", rules_file)
    with open(rules_file, "r", encoding="utf-8") as f:
        rules = [line.strip() for line in f.readlines() if line.strip()]
    _log_cache_hit("load_critical_rules")
    return rules


@lru_cache(maxsize=1)
def load_proficiency_levels() -> Dict[int, str]:
    """
    Load proficiency level mappings from JSON file.
    Cached for performance.
    """
    levels_file = PROMPTS_DIR / "proficiency_levels.json"
    _log_cache_miss("load_proficiency_levels", levels_file)
    with open(levels_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    _log_cache_hit("load_proficiency_levels")
    # Convert string keys to integers
    return {int(k): v for k, v in data.items()}


def format_critical_rules(rules: List[str]) -> str:
    """Format critical rules as numbered list."""
    return "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(rules)])


def load_all_prompts() -> Dict[str, Any]:
    """Load all prompt assets with logging."""
    logger.info("prompt_loader_bulk_load_start")
    data = {
        "system_prompt": load_system_prompt(),
        "critical_rules": load_critical_rules(),
        "proficiency_levels": load_proficiency_levels(),
    }
    logger.info("prompt_loader_bulk_load_complete", keys=list(data.keys()))
    return data


def clear_prompt_cache():
    """
    Clear the prompt cache.
    Useful for reloading prompts after changes during development.
    """
    logger.info("prompt_loader_cache_clear")
    load_system_prompt.cache_clear()
    load_critical_rules.cache_clear()
    load_proficiency_levels.cache_clear()

