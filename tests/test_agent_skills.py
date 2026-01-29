"""
Test Agent Skill System

Comprehensive tests for the Agent Skill system.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult
from alpha.skills.registry import SkillRegistry
from alpha.skills.installer import SkillInstaller
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.executor import SkillExecutor


class TestSkill(AgentSkill):
    """Test skill for unit testing."""

    async def initialize(self) -> bool:
        """Initialize test skill."""
        return True

    async def execute(self, **kwargs) -> SkillResult:
        """Execute test skill."""
        return SkillResult(
            success=True,
            output={"test": "success", "params": kwargs}
        )

    async def cleanup(self):
        """Cleanup test skill."""
        pass


async def test_skill_metadata():
    """Test skill metadata."""
    print("=" * 80)
    print("Test: Skill Metadata")
    print("=" * 80)

    metadata = SkillMetadata(
        name="test-skill",
        version="1.0.0",
        description="Test skill",
        author="Test Author",
        category="test",
        tags=["test", "example"],
        dependencies=["numpy"],
        python_version=">=3.8"
    )

    assert metadata.name == "test-skill"
    assert metadata.version == "1.0.0"
    assert metadata.category == "test"
    assert "test" in metadata.tags
    assert "numpy" in metadata.dependencies

    print("✓ Skill metadata creation and access works")
    print()


async def test_skill_registry():
    """Test skill registry."""
    print("=" * 80)
    print("Test: Skill Registry")
    print("=" * 80)

    registry = SkillRegistry()

    # Create test skill
    metadata = SkillMetadata(
        name="test-skill",
        version="1.0.0",
        description="Test skill",
        author="Test Author",
        category="test"
    )
    skill = TestSkill(metadata)

    # Register skill
    success = await registry.register(skill)
    assert success == True
    print("✓ Skill registration works")

    # List skills
    skills = registry.list_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "test-skill"
    print("✓ Skill listing works")

    # Get skill
    retrieved_skill = registry.get_skill("test-skill")
    assert retrieved_skill is not None
    assert retrieved_skill.metadata.name == "test-skill"
    print("✓ Skill retrieval works")

    # Execute skill
    result = await registry.execute_skill("test-skill", test_param="value")
    assert result.success == True
    assert result.output["test"] == "success"
    assert result.output["params"]["test_param"] == "value"
    print("✓ Skill execution works")

    # Unregister skill
    await registry.unregister("test-skill")
    assert registry.get_skill("test-skill") is None
    print("✓ Skill unregistration works")

    print()


async def test_skill_installer():
    """Test skill installer."""
    print("=" * 80)
    print("Test: Skill Installer")
    print("=" * 80)

    installer = SkillInstaller()
    example_skill_dir = Path(__file__).parent.parent / "examples" / "skills" / "example-skill"

    if not example_skill_dir.exists():
        print("⚠ Example skill not found, skipping installer test")
        print()
        return

    # Validate structure
    is_valid = installer._validate_skill_structure(example_skill_dir)
    assert is_valid == True
    print("✓ Skill structure validation works")

    # Load metadata
    metadata = installer._load_metadata(example_skill_dir)
    assert metadata is not None
    assert metadata.name == "example-skill"
    assert metadata.version == "1.0.0"
    print("✓ Skill metadata loading works")

    # Install skill (without dependencies to avoid external calls)
    skill = await installer.install(example_skill_dir, install_deps=False)
    assert skill is not None
    assert skill.metadata.name == "example-skill"
    print("✓ Skill installation works")

    # Test execution
    result = await skill.execute(operation="uppercase", text="hello world")
    assert result.success == True
    assert result.output["result"] == "HELLO WORLD"
    print("✓ Installed skill execution works")

    # Cleanup
    await skill.cleanup()
    print("✓ Skill cleanup works")

    print()


async def test_skill_marketplace():
    """Test skill marketplace."""
    print("=" * 80)
    print("Test: Skill Marketplace")
    print("=" * 80)

    marketplace = SkillMarketplace()

    # Clear cache
    marketplace.clear_cache()
    print("✓ Marketplace cache clearing works")

    # Test parsing registry data
    test_registry = {
        "skills": [
            {
                "name": "test-skill-1",
                "version": "1.0.0",
                "description": "Test skill 1",
                "author": "Test Author",
                "category": "test",
                "repository": "https://github.com/test/skill1"
            },
            {
                "name": "test-skill-2",
                "version": "2.0.0",
                "description": "Test skill 2",
                "author": "Test Author",
                "category": "utility",
                "tags": ["helper"],
                "repository": "https://github.com/test/skill2"
            }
        ]
    }

    marketplace._parse_registry(test_registry)
    assert len(marketplace.metadata_cache) == 2
    assert "test-skill-1" in marketplace.metadata_cache
    assert "test-skill-2" in marketplace.metadata_cache
    print("✓ Marketplace registry parsing works")

    # Test search
    results = await marketplace.search("test")
    assert len(results) >= 1
    print(f"✓ Marketplace search works (found {len(results)} results)")

    # Test search with category filter
    results = await marketplace.search("test", category="utility")
    assert len(results) >= 1
    assert all(r.category == "utility" for r in results)
    print("✓ Marketplace category filtering works")

    # Test get skill info
    skill_info = await marketplace.get_skill_info("test-skill-1")
    assert skill_info is not None
    assert skill_info.name == "test-skill-1"
    print("✓ Marketplace skill info retrieval works")

    print()


async def test_skill_executor():
    """Test skill executor."""
    print("=" * 80)
    print("Test: Skill Executor")
    print("=" * 80)

    registry = SkillRegistry()
    marketplace = SkillMarketplace()
    installer = SkillInstaller()
    executor = SkillExecutor(
        registry=registry,
        marketplace=marketplace,
        installer=installer,
        auto_install=False  # Disable auto-install for testing
    )

    # Register test skill
    metadata = SkillMetadata(
        name="test-skill",
        version="1.0.0",
        description="Test skill",
        author="Test Author",
        category="test"
    )
    skill = TestSkill(metadata)
    await registry.register(skill)

    # Execute skill
    result = await executor.execute("test-skill", test_param="value")
    assert result.success == True
    assert result.output["test"] == "success"
    print("✓ Executor skill execution works")

    # List installed skills
    skills = executor.list_installed_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "test-skill"
    print("✓ Executor skill listing works")

    # Discover skills
    marketplace.clear_cache()
    marketplace._parse_registry({
        "skills": [{
            "name": "discovered-skill",
            "version": "1.0.0",
            "description": "Discovered skill",
            "author": "Test",
            "category": "test",
            "repository": "https://github.com/test/skill"
        }]
    })

    discovered = await executor.discover_skills("discovered")
    assert len(discovered) >= 1
    print(f"✓ Executor skill discovery works (found {len(discovered)} skills)")

    # Cleanup
    await registry.cleanup_all()
    print("✓ Executor cleanup works")

    print()


async def run_all_tests():
    """Run all tests."""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "AGENT SKILL SYSTEM TESTS")
    print("=" * 80)
    print()

    try:
        await test_skill_metadata()
        await test_skill_registry()
        await test_skill_installer()
        await test_skill_marketplace()
        await test_skill_executor()

        print("=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print()

    except AssertionError as e:
        print("=" * 80)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 80)
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print("=" * 80)
        print(f"✗ ERROR: {e}")
        print("=" * 80)
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
