"""AI context and prompt generation."""
from app.core.resources import linkedin, summary, facts, style
from app.core.prompt_loader import (
    load_system_prompt,
    load_critical_rules,
    load_proficiency_levels,
    format_critical_rules
)
from datetime import datetime


full_name = facts["full_name"]
name = facts["name"]


def format_tech_item(item, proficiency_levels):
    """Convert a tech item with proficiency number to natural language."""
    item_name = item.get("name", "")
    proficiency = item.get("proficiency", 3)
    level_text = proficiency_levels.get(proficiency, "experience with")
    return f"{item_name} ({level_text})"


def format_tech_stack(tech_stack, proficiency_levels):
    """Format the entire tech stack with natural language proficiency levels."""
    formatted = {}
    for category, items in tech_stack.items():
        formatted[category] = [format_tech_item(item, proficiency_levels) for item in items]
    return formatted


def get_formatted_facts():
    """Get facts with formatted tech stack."""
    proficiency_levels = load_proficiency_levels()
    formatted = facts.copy()
    if "tech_stack" in formatted:
        formatted["tech_stack"] = format_tech_stack(formatted["tech_stack"], proficiency_levels)
    return formatted


def prompt():
    """
    Generate the system prompt for the AI.
    Loads template and data from external files.
    """
    # Load template and rules
    template = load_system_prompt()
    rules = load_critical_rules()
    
    # Format variables
    formatted_facts = get_formatted_facts()
    critical_rules_formatted = format_critical_rules(rules)
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Fill in template
    return template.format(
        full_name=full_name,
        name=name,
        formatted_facts=formatted_facts,
        summary=summary,
        linkedin=linkedin,
        style=style,
        current_datetime=current_datetime,
        num_rules=len(rules),
        critical_rules=critical_rules_formatted
    )