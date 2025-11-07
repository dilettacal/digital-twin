"""Data loading and caching utilities for personal data files."""
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache
from pypdf import PdfReader

# Get the data directory path (backend/data)
DATA_DIR = Path(__file__).parent.parent.parent / "data"


# ============================================================================
# Core Data Loaders (JSON)
# ============================================================================

@lru_cache(maxsize=1)
def load_facts() -> Dict[str, Any]:
    """
    Load canonical facts from facts.json.
    Cached for performance.
    """
    facts_file = DATA_DIR / "facts.json"
    with open(facts_file, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_sources() -> Dict[str, Any]:
    """
    Load document registry from sources.json.
    Cached for performance.
    """
    sources_file = DATA_DIR / "sources.json"
    with open(sources_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# Text Data Loaders
# ============================================================================

@lru_cache(maxsize=1)
def load_summary() -> str:
    """
    Load narrative summary from summary.txt.
    Cached for performance.
    """
    summary_file = DATA_DIR / "summary.txt"
    with open(summary_file, "r", encoding="utf-8") as f:
        return f.read()


@lru_cache(maxsize=1)
def load_style() -> str:
    """
    Load communication style guide from style.txt.
    Cached for performance.
    """
    style_file = DATA_DIR / "style.txt"
    with open(style_file, "r", encoding="utf-8") as f:
        return f.read()


@lru_cache(maxsize=1)
def load_me() -> str:
    """
    Load persona and guardrails from me.txt.
    Cached for performance.
    """
    me_file = DATA_DIR / "me.txt"
    with open(me_file, "r", encoding="utf-8") as f:
        return f.read()


@lru_cache(maxsize=1)
def load_resume() -> str:
    """
    Load markdown resume from resume.md.
    Cached for performance.
    """
    resume_file = DATA_DIR / "resume.md"
    try:
        with open(resume_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


# ============================================================================
# YAML Data Loaders
# ============================================================================

@lru_cache(maxsize=1)
def load_skills() -> Dict[str, Any]:
    """
    Load structured skills inventory from skills.yml.
    Cached for performance.
    """
    skills_file = DATA_DIR / "skills.yml"
    with open(skills_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_education() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load structured education history from education.yml.
    Cached for performance.
    """
    education_file = DATA_DIR / "education.yml"
    with open(education_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_experience() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load structured professional experience from experience.yml.
    Cached for performance.
    """
    experience_file = DATA_DIR / "experience.yml"
    with open(experience_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_qna() -> Dict[str, List[Dict[str, str]]]:
    """
    Load FAQ pairs from qna.yml.
    Cached for performance.
    """
    qna_file = DATA_DIR / "qna.yml"
    with open(qna_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================================
# Optional/Heavy Loaders (LinkedIn PDF)
# ============================================================================

@lru_cache(maxsize=1)
def load_linkedin(skip_on_error: bool = True) -> str:
    """
    Load LinkedIn profile from PDF.
    This is an expensive operation, so it's cached and can be skipped on error.
    
    Args:
        skip_on_error: If True, returns fallback message on error instead of raising
    
    Returns:
        Extracted text from LinkedIn PDF or fallback message
    """
    linkedin_file = DATA_DIR / "linkedin.pdf"
    
    try:
        reader = PdfReader(linkedin_file)
        linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                linkedin += text
        return linkedin if linkedin else "LinkedIn profile not available"
    except FileNotFoundError:
        if skip_on_error:
            return "LinkedIn profile not available"
        raise
    except Exception as e:
        if skip_on_error:
            return f"LinkedIn profile not available (error: {type(e).__name__})"
        raise


# ============================================================================
# Convenience Functions
# ============================================================================

def get_person_name() -> str:
    """Get the person's preferred name."""
    facts = load_facts()
    return facts.get("name", "")


def get_person_full_name() -> str:
    """Get the person's full name."""
    facts = load_facts()
    return facts.get("full_name", "")


def get_all_data(include_linkedin: bool = False) -> Dict[str, Any]:
    """
    Load all data files into a single dictionary.
    
    Args:
        include_linkedin: If True, includes the LinkedIn PDF (slow)
    
    Returns:
        Dictionary with all loaded data
    """
    data = {
        "facts": load_facts(),
        "summary": load_summary(),
        "style": load_style(),
        "me": load_me(),
        "skills": load_skills(),
        "education": load_education(),
        "experience": load_experience(),
        "qna": load_qna(),
        "sources": load_sources(),
        "resume": load_resume(),
    }
    
    if include_linkedin:
        data["linkedin"] = load_linkedin()
    
    return data


def clear_data_cache():
    """
    Clear all data caches.
    Useful for reloading data after changes during development.
    """
    load_facts.cache_clear()
    load_sources.cache_clear()
    load_summary.cache_clear()
    load_style.cache_clear()
    load_me.cache_clear()
    load_resume.cache_clear()
    load_skills.cache_clear()
    load_education.cache_clear()
    load_experience.cache_clear()
    load_qna.cache_clear()
    load_linkedin.cache_clear()


# ============================================================================
# Backward Compatibility Exports
# ============================================================================

# Module-level exports for backward compatibility
facts = load_facts()
summary = load_summary()
style = load_style()
linkedin = load_linkedin()

# For easy access
full_name = facts.get("full_name", "")
name = facts.get("name", "")

