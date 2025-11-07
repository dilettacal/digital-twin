"""
Legacy resource loader - now imports from data_loader.

This file is kept for backward compatibility.
New code should import directly from data_loader instead.
"""
from app.core.data_loader import (
    load_facts,
    load_summary,
    load_style,
    load_linkedin,
    load_skills,
    load_education,
    load_experience,
    load_qna,
    load_sources,
    load_me,
    load_resume,
    get_person_name,
    get_person_full_name,
)

# Backward compatible exports
facts = load_facts()
summary = load_summary()
style = load_style()
linkedin = load_linkedin()

# Additional exports for convenience
full_name = get_person_full_name()
name = get_person_name()