"""
Test Preinstalled Builtin Skills

Test that all builtin skills are correctly preinstalled and functional.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.skills.registry import SkillRegistry
from alpha.skills.installer import SkillInstaller
from alpha.skills import preinstall_builtin_skills


async def test_preinstall():
    """Test preinstallation of builtin skills."""
    print("=" * 80)
    print("Testing Builtin Skills Preinstallation")
    print("=" * 80)
    print()

    registry = SkillRegistry()
    installer = SkillInstaller()

    # Preinstall builtin skills
    print("1. Preinstalling builtin skills...")
    installed_count = await preinstall_builtin_skills(registry, installer)
    print(f"   ✓ Installed {installed_count} skills\n")

    # List installed skills
    print("2. Listing installed skills...")
    skills = registry.list_skills()
    for skill in skills:
        print(f"   - {skill['name']} v{skill['version']}: {skill['description']}")
    print()

    # Test each skill
    print("3. Testing skills...")
    print()

    # Test text-processing
    if registry.get_skill("text-processing"):
        print("   Testing text-processing skill...")
        result = await registry.execute_skill(
            "text-processing",
            operation="uppercase",
            text="hello world"
        )
        assert result.success == True
        assert result.output["result"] == "HELLO WORLD"
        print("   ✓ text-processing works")
        print()

    # Test json-processor
    if registry.get_skill("json-processor"):
        print("   Testing json-processor skill...")
        result = await registry.execute_skill(
            "json-processor",
            operation="parse",
            json_str='{"name": "Alpha", "version": "1.0"}'
        )
        assert result.success == True
        assert result.output["result"]["name"] == "Alpha"
        print("   ✓ json-processor works")
        print()

    # Test data-analyzer
    if registry.get_skill("data-analyzer"):
        print("   Testing data-analyzer skill...")
        result = await registry.execute_skill(
            "data-analyzer",
            operation="mean",
            data=[1, 2, 3, 4, 5]
        )
        assert result.success == True
        assert result.output["mean"] == 3.0
        print("   ✓ data-analyzer works")
        print()

    # Cleanup
    await registry.cleanup_all()

    print("=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80)
    print()

    return installed_count


if __name__ == "__main__":
    try:
        count = asyncio.run(test_preinstall())
        print(f"Successfully preinstalled and tested {count} builtin skills")
        sys.exit(0)
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
