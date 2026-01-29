"""
Test script for automatic skill system.

Tests:
1. SkillMatcher - Find relevant skills
2. SkillDownloader - Auto-install skills
3. SkillLoader - Load skill context
4. AutoSkillManager - End-to-end workflow
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alpha.skills.auto_manager import AutoSkillManager


async def test_skill_matching():
    """Test skill matching functionality."""
    print("=" * 60)
    print("Test 1: Skill Matching")
    print("=" * 60)

    manager = AutoSkillManager(auto_install=False, auto_load=False)
    await manager.initialize()

    test_queries = [
        "Help me build a React component",
        "Create a PDF document",
        "Design a beautiful UI",
        "Optimize my database queries",
        "Write SEO-friendly content",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        matches = await manager.suggest_skills(query, max_suggestions=3)

        if matches:
            print(f"  Found {len(matches)} matching skills:")
            for i, match in enumerate(matches, 1):
                status = "✓ installed" if match['installed'] else "✗ not installed"
                print(f"    {i}. {match['name']} ({status})")
                print(f"       - Score: {match['score']:.1f}, Installs: {match['installs']:,}")
        else:
            print("  No matches found")

    print("\n✅ Skill matching test completed")


async def test_auto_skill_workflow():
    """Test end-to-end automatic skill workflow."""
    print("\n" + "=" * 60)
    print("Test 2: Automatic Skill Workflow")
    print("=" * 60)

    manager = AutoSkillManager(auto_install=True, auto_load=True)
    await manager.initialize()

    # Test query that should match a skill
    query = "Help me create a React component with best practices"
    print(f"\nProcessing query: '{query}'")

    result = await manager.process_query(query)

    if result:
        print(f"✅ Skill found and loaded: {result['skill_name']}")
        print(f"   - Source: {result['skill_source']}")
        print(f"   - Score: {result['score']:.1f}")
        print(f"   - Installs: {result['installs']:,}")
        print(f"\n   Context preview:")
        context_preview = result['context'][:200] + "..." if len(result['context']) > 200 else result['context']
        print(f"   {context_preview}")
    else:
        print("❌ No suitable skill found or loaded")

    # List installed skills
    print("\nCurrently installed skills:")
    installed = manager.list_installed_skills()
    for skill in installed:
        print(f"  - {skill['name']}: {skill['description'][:60]}...")

    print("\n✅ Automatic workflow test completed")


async def test_specific_skill():
    """Test loading a specific skill."""
    print("\n" + "=" * 60)
    print("Test 3: Specific Skill Loading")
    print("=" * 60)

    manager = AutoSkillManager(auto_install=True, auto_load=True)
    await manager.initialize()

    # Test loading a popular skill
    skill_name = "find-skills"
    print(f"\nLoading skill: {skill_name}")

    context = await manager.get_skill_context(skill_name)

    if context:
        print(f"✅ Successfully loaded skill context")
        print(f"\nContext length: {len(context)} characters")
        print(f"Preview:\n{context[:300]}...")
    else:
        print(f"❌ Failed to load skill context")

    print("\n✅ Specific skill loading test completed")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AUTOMATIC SKILL SYSTEM TEST SUITE")
    print("=" * 60)

    try:
        # Run tests
        await test_skill_matching()
        await test_auto_skill_workflow()
        await test_specific_skill()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
