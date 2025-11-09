"""Data loading and caching utilities for personal data files."""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from functools import lru_cache
from pypdf import PdfReader
from app.core.logging import get_logger

logger = get_logger(__name__)


def _log_cache_hit(loader_name: str) -> None:
    logger.debug("data_loader_cache_hit", loader=loader_name)


def _log_cache_miss(loader_name: str, path: Path) -> None:
    logger.info("data_loader_load", loader=loader_name, path=str(path))


# Determine data directories (allow overrides for testing)
DEFAULT_BASE_DATA_DIR = Path(__file__).parent.parent.parent / "data"
BASE_DATA_DIR = Path(os.environ.get("DIGITAL_TWIN_DATA_DIR", DEFAULT_BASE_DATA_DIR))
PERSONAL_DATA_DIR = Path(
    os.environ.get("DIGITAL_TWIN_PERSONAL_DATA_DIR", BASE_DATA_DIR / "personal_data")
)

if not PERSONAL_DATA_DIR.exists():
    raise FileNotFoundError(f"Personal data directory not found at {PERSONAL_DATA_DIR}")


# ============================================================================
# Core Data Loaders (JSON)
# ============================================================================

@lru_cache(maxsize=1)
def load_facts() -> Dict[str, Any]:
    """
    Load canonical facts from facts.json.
    Cached for performance.
    """
    facts_file = PERSONAL_DATA_DIR / "facts.json"
    _log_cache_miss("load_facts", facts_file)
    with open(facts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    _log_cache_hit("load_facts")
    return data


@lru_cache(maxsize=1)
def load_sources() -> Dict[str, Any]:
    """
    Load document registry from sources.json.
    Cached for performance.
    """
    sources_file = PERSONAL_DATA_DIR / "sources.json"
    _log_cache_miss("load_sources", sources_file)
    with open(sources_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    _log_cache_hit("load_sources")
    return data


# ============================================================================
# Text Data Loaders
# ============================================================================

@lru_cache(maxsize=1)
def load_summary() -> str:
    """
    Load narrative summary from summary.txt.
    Cached for performance.
    """
    summary_file = PERSONAL_DATA_DIR / "summary.txt"
    _log_cache_miss("load_summary", summary_file)
    with open(summary_file, "r", encoding="utf-8") as f:
        data = f.read()
    _log_cache_hit("load_summary")
    return data


@lru_cache(maxsize=1)
def load_style() -> str:
    """
    Load communication style guide from style.txt.
    Cached for performance.
    """
    style_file = PERSONAL_DATA_DIR / "style.txt"
    _log_cache_miss("load_style", style_file)
    with open(style_file, "r", encoding="utf-8") as f:
        data = f.read()
    _log_cache_hit("load_style")
    return data


@lru_cache(maxsize=1)
def load_me() -> str:
    """
    Load persona and guardrails from me.txt.
    Cached for performance.
    """
    me_file = PERSONAL_DATA_DIR / "me.txt"
    _log_cache_miss("load_me", me_file)
    with open(me_file, "r", encoding="utf-8") as f:
        data = f.read()
    _log_cache_hit("load_me")
    return data


@lru_cache(maxsize=1)
def load_resume() -> str:
    """
    Load markdown resume from resume.md.
    Cached for performance.
    """
    resume_file = PERSONAL_DATA_DIR / "resume.md"
    _log_cache_miss("load_resume", resume_file)
    try:
        with open(resume_file, "r", encoding="utf-8") as f:
            data = f.read()
        _log_cache_hit("load_resume")
        return data
    except FileNotFoundError:
        logger.info("data_loader_optional_missing", loader="load_resume", path=str(resume_file))
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
    skills_file = PERSONAL_DATA_DIR / "skills.yml"
    _log_cache_miss("load_skills", skills_file)
    with open(skills_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _log_cache_hit("load_skills")
    return data


@lru_cache(maxsize=1)
def load_education() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load structured education history from education.yml.
    Cached for performance.
    """
    education_file = PERSONAL_DATA_DIR / "education.yml"
    _log_cache_miss("load_education", education_file)
    with open(education_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _log_cache_hit("load_education")
    return data


@lru_cache(maxsize=1)
def load_experience() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load structured professional experience from experience.yml.
    Cached for performance.
    """
    experience_file = PERSONAL_DATA_DIR / "experience.yml"
    _log_cache_miss("load_experience", experience_file)
    with open(experience_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _log_cache_hit("load_experience")
    return data


@lru_cache(maxsize=1)
def load_qna() -> Dict[str, List[Dict[str, str]]]:
    """
    Load FAQ pairs from qna.yml.
    Cached for performance.
    """
    qna_file = PERSONAL_DATA_DIR / "qna.yml"
    _log_cache_miss("load_qna", qna_file)
    with open(qna_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _log_cache_hit("load_qna")
    return data


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
    linkedin_file = PERSONAL_DATA_DIR / "linkedin.pdf"
    _log_cache_miss("load_linkedin", linkedin_file)

    try:
        reader = PdfReader(linkedin_file)
        linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                linkedin += text
        result = linkedin if linkedin else "LinkedIn profile not available"
        _log_cache_hit("load_linkedin")
        return result
    except FileNotFoundError:
        if skip_on_error:
            logger.info("data_loader_optional_missing", loader="load_linkedin", path=str(linkedin_file))
            return "LinkedIn profile not available"
        raise
    except Exception as e:
        if skip_on_error:
            logger.warning(
                "data_loader_linkedin_error",
                loader="load_linkedin",
                path=str(linkedin_file),
                error=type(e).__name__,
            )
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
    logger.info("data_loader_bulk_load_start", include_linkedin=include_linkedin)
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

    logger.info("data_loader_bulk_load_complete", keys=list(data.keys()))
    return data


def clear_data_cache():
    """
    Clear all data caches.
    Useful for reloading data after changes during development.
    """
    logger.info("data_loader_cache_clear")
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

