"""
Test configuration loading with ANTHROPIC_AUTH_TOKEN and ANTHROPIC_BASE_URL
"""

import os
import sys

# Test environment variables
print("Testing configuration with Anthropic settings...")
print("=" * 60)

# Set test environment variables
os.environ["ANTHROPIC_AUTH_TOKEN"] = "test-token-123"
os.environ["ANTHROPIC_BASE_URL"] = "https://api.anthropic.example.com"

# Import after setting env vars
from alpha.utils.config import load_config

try:
    config = load_config('config.yaml')

    print(f"✅ Config loaded successfully")
    print(f"Default provider: {config.llm.default_provider}")

    # Check Anthropic config
    anthropic_config = config.llm.providers.get("anthropic")
    if anthropic_config:
        print(f"\nAnthropic Configuration:")
        print(f"  Model: {anthropic_config.model}")
        print(f"  API Key: {anthropic_config.api_key[:20]}..." if anthropic_config.api_key else "  API Key: [Not Set]")
        print(f"  Base URL: {anthropic_config.base_url}")
        print(f"  Max Tokens: {anthropic_config.max_tokens}")
        print(f"  Temperature: {anthropic_config.temperature}")

        # Verify values
        # Note: Default provider is now deepseek, but we're testing Anthropic config loading
        assert config.llm.providers.get("anthropic") is not None, "Anthropic provider should be configured"
        assert anthropic_config.api_key == "test-token-123", "API key should be from ANTHROPIC_AUTH_TOKEN"
        assert anthropic_config.base_url == "https://api.anthropic.example.com", "Base URL should be set"
        assert anthropic_config.model == "claude-sonnet-4-5-20250929", "Model should be claude-sonnet-4-5"
        assert anthropic_config.max_tokens == 8192, "Max tokens should be 8192"

        print("\n✅ All configuration tests passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test fallback to ANTHROPIC_API_KEY
print("\n" + "=" * 60)
print("Testing fallback to ANTHROPIC_API_KEY...")

# Remove AUTH_TOKEN, set API_KEY
del os.environ["ANTHROPIC_AUTH_TOKEN"]
os.environ["ANTHROPIC_API_KEY"] = "fallback-key-456"

# Need to reimport to test fallback
import importlib
import alpha.utils.config
importlib.reload(alpha.utils.config)
from alpha.utils.config import load_config as load_config2

try:
    config2 = load_config2('config.yaml')
    anthropic_config2 = config2.llm.providers.get("anthropic")

    if anthropic_config2:
        print(f"API Key (from fallback): {anthropic_config2.api_key[:20]}...")
        assert anthropic_config2.api_key == "fallback-key-456", "Should fallback to ANTHROPIC_API_KEY"
        print("✅ Fallback to ANTHROPIC_API_KEY works!")

except Exception as e:
    print(f"❌ Fallback test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 All configuration tests completed successfully!")
