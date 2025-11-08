# Prompt Templates

This directory contains prompt templates used by the AI Digital Twin.

## Files

### `system_prompt.txt`
The main system prompt that defines the AI's role and behavior. Uses template variables:
- `{full_name}` - The person's full name
- `{name}` - The person's preferred name
- `{formatted_facts}` - Formatted facts about the person
- `{summary}` - Personal summary notes
- `{linkedin}` - LinkedIn profile content
- `{style}` - Communication style notes
- `{current_datetime}` - Current date and time
- `{num_rules}` - Number of critical rules
- `{critical_rules}` - Formatted list of critical rules

### `critical_rules.txt`
Critical rules that the AI must follow. Each rule on a separate line.
These are automatically numbered when loaded into the system prompt.

### `proficiency_levels.json`
Mapping of proficiency level numbers (1-5) to their natural language descriptions.
Used to format technical skills in conversational language.

## Usage

These files are loaded by `app/core/context.py` and cached for performance.
To update the AI's behavior, simply edit these files - no code changes needed.

## Best Practices

1. **Keep prompts clear and concise**
2. **Test changes thoroughly** before deploying
3. **Version control** all prompt changes
4. **Document** why significant changes were made
5. **A/B test** major prompt modifications when possible

