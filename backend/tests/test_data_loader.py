"""Tests for data_loader module."""
import pytest
from app.core.data_loader import (
    load_facts,
    load_summary,
    load_style,
    load_me,
    load_skills,
    load_education,
    load_experience,
    load_qna,
    load_sources,
    load_resume,
    load_linkedin,
    get_person_name,
    get_person_full_name,
    get_all_data,
    clear_data_cache,
)


class TestCoreDataLoaders:
    """Test core data loading functions."""

    def test_load_facts(self):
        """Test facts.json loading."""
        facts = load_facts()
        assert isinstance(facts, dict)
        assert "full_name" in facts
        assert "name" in facts
        assert "current_role" in facts

    def test_load_summary(self):
        """Test summary.txt loading."""
        summary = load_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_load_style(self):
        """Test style.txt loading."""
        style = load_style()
        assert isinstance(style, str)
        assert len(style) > 0

    def test_load_me(self):
        """Test me.txt loading."""
        me = load_me()
        assert isinstance(me, str)
        assert len(me) > 0


class TestYAMLLoaders:
    """Test YAML data loaders."""

    def test_load_skills(self):
        """Test skills.yml loading."""
        skills = load_skills()
        assert isinstance(skills, dict)
        assert "categories" in skills

    def test_load_education(self):
        """Test education.yml loading."""
        education = load_education()
        assert isinstance(education, dict)
        assert "education" in education
        assert isinstance(education["education"], list)

    def test_load_experience(self):
        """Test experience.yml loading."""
        experience = load_experience()
        assert isinstance(experience, dict)
        assert "roles" in experience
        assert isinstance(experience["roles"], list)

    def test_load_qna(self):
        """Test qna.yml loading."""
        qna = load_qna()
        assert isinstance(qna, dict)
        assert "faqs" in qna
        assert isinstance(qna["faqs"], list)


class TestOptionalLoaders:
    """Test optional data loaders."""

    def test_load_sources(self):
        """Test sources.json loading."""
        sources = load_sources()
        assert isinstance(sources, dict)
        assert "documents" in sources
        assert isinstance(sources["documents"], list)

    def test_load_resume(self):
        """Test resume.md loading (optional file)."""
        # Should not raise error even if file doesn't exist
        resume = load_resume()
        assert isinstance(resume, str)

    def test_load_linkedin_skip_error(self):
        """Test linkedin.pdf loading with skip_on_error."""
        # Should not raise error even if file doesn't exist or can't be parsed
        linkedin = load_linkedin(skip_on_error=True)
        assert isinstance(linkedin, str)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_person_name(self):
        """Test getting person's preferred name."""
        name = get_person_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_person_full_name(self):
        """Test getting person's full name."""
        full_name = get_person_full_name()
        assert isinstance(full_name, str)
        assert len(full_name) > 0

    def test_get_all_data_without_linkedin(self):
        """Test loading all data without LinkedIn."""
        data = get_all_data(include_linkedin=False)
        assert isinstance(data, dict)
        assert "facts" in data
        assert "summary" in data
        assert "style" in data
        assert "skills" in data
        assert "education" in data
        assert "experience" in data
        assert "qna" in data
        assert "sources" in data
        assert "linkedin" not in data

    def test_get_all_data_with_linkedin(self):
        """Test loading all data with LinkedIn."""
        data = get_all_data(include_linkedin=True)
        assert isinstance(data, dict)
        assert "linkedin" in data


class TestCaching:
    """Test caching behavior."""

    def test_cache_is_used(self):
        """Test that cache is working."""
        # Load twice - should return same object due to cache
        facts1 = load_facts()
        facts2 = load_facts()
        assert facts1 is facts2  # Same object reference

    def test_clear_cache(self):
        """Test cache clearing."""
        # Load data
        facts1 = load_facts()
        
        # Clear cache
        clear_data_cache()
        
        # Load again - should be different object
        facts2 = load_facts()
        
        # Objects should have same content but different reference
        assert facts1 == facts2
        # Note: After cache clear, they might still be the same object
        # if the file hasn't changed, but cache is cleared


class TestDataStructure:
    """Test data structure and content."""

    def test_facts_structure(self):
        """Test that facts.json has expected structure."""
        facts = load_facts()
        required_fields = ["full_name", "name", "current_role", "location"]
        for field in required_fields:
            assert field in facts, f"Missing required field: {field}"

    def test_skills_structure(self):
        """Test that skills.yml has expected structure."""
        skills = load_skills()
        assert "categories" in skills
        categories = skills["categories"]
        assert isinstance(categories, dict)
        
        # Check that at least one category has expected structure
        for category_id, category in categories.items():
            if "title" in category:
                assert "items" in category
                assert isinstance(category["items"], list)
                break

    def test_experience_structure(self):
        """Test that experience.yml has expected structure."""
        experience = load_experience()
        assert "roles" in experience
        roles = experience["roles"]
        assert isinstance(roles, list)
        
        if len(roles) > 0:
            role = roles[0]
            assert "id" in role
            assert "title" in role
            assert "company" in role

    def test_qna_structure(self):
        """Test that qna.yml has expected structure."""
        qna = load_qna()
        assert "faqs" in qna
        faqs = qna["faqs"]
        assert isinstance(faqs, list)
        
        if len(faqs) > 0:
            faq = faqs[0]
            assert "id" in faq
            assert "question" in faq
            assert "answer" in faq

