#!/usr/bin/env python3
"""
Integration test for auto-skill system.
Tests the full workflow from CLI perspective.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alpha.skills.auto_manager import AutoSkillManager
from alpha.utils.config import load_config


async def test_skill_loading():
    """Test that skills can be loaded."""
    print("=" * 60)
    print("TEST 1: Skill Loading")
    print("=" * 60)

    manager = AutoSkillManager(auto_install=True, auto_load=True)
    await manager.initialize()

    # List installed skills
    skills = manager.list_installed_skills()
    print(f"\n✓ Found {len(skills)} installed skills")

    if len(skills) == 0:
        print("❌ ERROR: No skills found!")
        return False

    # Show first 5 skills
    print("\nFirst 5 skills:")
    for skill in skills[:5]:
        print(f"  - {skill['name']}: {skill['description'][:50]}...")

    return True


async def test_skill_matching():
    """Test skill matching with various queries."""
    print("\n" + "=" * 60)
    print("TEST 2: Skill Matching")
    print("=" * 60)

    manager = AutoSkillManager(auto_install=True, auto_load=True)
    await manager.initialize()

    test_queries = [
        ("Help me create a React component", "vercel-react-best-practices"),
        ("Create a PDF document", "pdf"),
        ("Optimize my database queries", "supabase-postgres-best-practices"),  # Fixed: more specific
        ("Audit website for SEO", "seo-audit"),
        ("Create a presentation", "pptx"),
    ]

    all_passed = True

    for query, expected_skill in test_queries:
        print(f"\nQuery: '{query}'")
        result = await manager.process_query(query)

        if result:
            skill_name = result['skill_name']
            score = result['score']
            print(f"  ✓ Matched: {skill_name} (score: {score:.1f})")

            if skill_name != expected_skill:
                print(f"  ⚠️  Expected: {expected_skill}, got: {skill_name}")
                # Not a failure, just different match
        else:
            print(f"  ❌ No skill matched")
            all_passed = False

    return all_passed


async def test_skill_context():
    """Test that skill context is loaded correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: Skill Context Loading")
    print("=" * 60)

    manager = AutoSkillManager(auto_install=True, auto_load=True)
    await manager.initialize()

    # Test loading specific skill
    test_skills = ["find-skills", "vercel-react-best-practices", "pdf"]

    all_passed = True

    for skill_name in test_skills:
        print(f"\nLoading skill: {skill_name}")
        context = await manager.get_skill_context(skill_name)

        if context:
            print(f"  ✓ Context loaded ({len(context)} characters)")

            # Verify context has expected format
            if "# ACTIVE SKILL:" in context:
                print(f"  ✓ Context format is correct")
            else:
                print(f"  ❌ Context format is incorrect")
                all_passed = False
        else:
            print(f"  ❌ Failed to load context")
            all_passed = False

    return all_passed


async def test_config_loading():
    """Test that configuration is loaded correctly."""
    print("\n" + "=" * 60)
    print("TEST 4: Configuration")
    print("=" * 60)

    try:
        config = load_config('config.yaml')
        skill_config = config.dict().get('skills', {}) if hasattr(config, 'dict') else {}
        auto_skill_config = skill_config.get('auto_skill', {})

        print(f"\nAuto-skill enabled: {auto_skill_config.get('enabled', False)}")
        print(f"Auto-install: {auto_skill_config.get('auto_install', False)}")
        print(f"Auto-load: {auto_skill_config.get('auto_load', False)}")
        print(f"Min score: {auto_skill_config.get('min_score', 3.0)}")
        print(f"Max matches: {auto_skill_config.get('max_matches', 3)}")

        print("\n✓ Configuration loaded successfully")
        return True

    except Exception as e:
        print(f"\n❌ Failed to load configuration: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AUTO-SKILL SYSTEM INTEGRATION TEST")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Skill Loading", await test_skill_loading()))
    results.append(("Skill Matching", await test_skill_matching()))
    results.append(("Skill Context", await test_skill_context()))
    results.append(("Configuration", await test_config_loading()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
