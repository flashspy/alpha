# Agent Skill System Documentation

## Overview

The Agent Skill System is a powerful feature of Alpha that enables **dynamic capability expansion** through auto-discovery, installation, and execution of skills. Unlike built-in tools, skills are **modular, versioned, and can be distributed independently**.

## Architecture

### Core Components

1. **AgentSkill** - Base class for all skills
2. **SkillRegistry** - Manages installed skills and their lifecycle
3. **SkillMarketplace** - Discovers and downloads skills from repositories
4. **SkillInstaller** - Installs skills and manages dependencies
5. **SkillExecutor** - Executes skills with auto-install support

### Component Interactions

```
User Request
     ↓
SkillExecutor
     ├─→ SkillRegistry (check if installed)
     ├─→ SkillMarketplace (search and download if not found)
     ├─→ SkillInstaller (install from downloaded package)
     └─→ Execute skill
```

## Creating a Skill

### Skill Structure

Every skill consists of:

```
my-skill/
├── skill.yaml        # Metadata (required)
├── skill.py          # Implementation (required)
├── README.md         # Documentation (optional)
└── requirements.txt  # Dependencies (optional)
```

### skill.yaml

```yaml
name: my-skill
version: "1.0.0"
description: "My awesome skill"
author: "Your Name"
category: "utility"  # e.g., utility, data, ai, web, etc.
tags:
  - text-processing
  - helper
dependencies:
  - numpy
  - pandas
python_version: ">=3.8"
homepage: "https://github.com/user/my-skill"
repository: "https://github.com/user/my-skill"
license: "MIT"
```

### skill.py

```python
from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult

class MySkill(AgentSkill):
    """My custom skill."""

    async def initialize(self) -> bool:
        """Initialize the skill (called once after installation)."""
        # Setup resources, load models, etc.
        return True

    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill.

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult with success status and output
        """
        try:
            # Your skill logic here
            result = self._do_something(kwargs)

            return SkillResult(
                success=True,
                output=result
            )

        except Exception as e:
            return SkillResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def cleanup(self):
        """Clean up resources (called when skill is unloaded)."""
        pass

    def get_schema(self):
        """Define parameter schema for validation."""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter 1"},
                "param2": {"type": "number", "description": "Parameter 2"}
            },
            "required": ["param1"]
        }
```

## Using Skills

### In Chat (Automatic Discovery)

Skills are automatically discovered and installed when you use them:

```
User: Convert this text to uppercase: "hello world"

Alpha: I'll use the text-processing skill for this.

SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

Alpha: The result is "HELLO WORLD"
```

### Manual Installation

```bash
# In Alpha CLI
skills                    # List installed skills
search skill text        # Search for skills
```

### Programmatic Usage

```python
from alpha.skills.executor import SkillExecutor
from alpha.skills.registry import SkillRegistry
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.installer import SkillInstaller

# Setup
registry = SkillRegistry()
marketplace = SkillMarketplace()
installer = SkillInstaller()
executor = SkillExecutor(
    registry=registry,
    marketplace=marketplace,
    installer=installer,
    auto_install=True
)

# Execute skill (auto-installs if not found)
result = await executor.execute(
    "my-skill",
    param1="value1",
    param2=42
)

if result.success:
    print(result.output)
else:
    print(f"Error: {result.error}")
```

## Skill Marketplace

### Default Sources

The marketplace searches skills from:

1. **Official Alpha Skill Repository** - `https://github.com/alpha-ai/skills`
2. **Local Skills Directory** - `~/.alpha/local_skills/`

### Adding Custom Sources

```python
marketplace.add_source("https://my-company.com/skills/registry.json")
```

### Registry Format

```json
{
  "skills": [
    {
      "name": "my-skill",
      "version": "1.0.0",
      "description": "My skill",
      "author": "Author Name",
      "category": "utility",
      "tags": ["helper"],
      "repository": "https://github.com/user/my-skill"
    }
  ]
}
```

## Skill Categories

Recommended categories:

- **utility** - General utility functions
- **data** - Data processing and transformation
- **ai** - AI/ML capabilities
- **web** - Web scraping and interaction
- **file** - File operations
- **image** - Image processing
- **video** - Video processing
- **audio** - Audio processing
- **nlp** - Natural language processing
- **api** - API integrations

## Best Practices

### Skill Design

1. **Single Responsibility** - Each skill should do one thing well
2. **Clear Parameters** - Use descriptive parameter names and provide schemas
3. **Error Handling** - Always return clear error messages
4. **Resource Management** - Clean up resources in `cleanup()`
5. **Documentation** - Include clear README with examples

### Performance

1. **Lazy Loading** - Initialize heavy resources in `initialize()`, not `__init__()`
2. **Async Operations** - Use async/await for I/O operations
3. **Caching** - Cache expensive computations
4. **Timeout Handling** - Implement timeouts for long operations

### Security

1. **Input Validation** - Always validate input parameters
2. **Sandboxing** - Skills run with limited permissions (future enhancement)
3. **No Secrets in Code** - Use environment variables for sensitive data
4. **Dependency Pinning** - Specify exact versions in requirements.txt

## Testing Skills

### Unit Testing

```python
import pytest
from alpha.skills.installer import SkillInstaller

@pytest.mark.asyncio
async def test_my_skill():
    installer = SkillInstaller()
    skill = await installer.install(Path("path/to/my-skill"), install_deps=False)

    result = await skill.execute(param1="test")

    assert result.success == True
    assert result.output["expected_key"] == "expected_value"
```

### Integration Testing

```python
from alpha.skills.executor import SkillExecutor

@pytest.mark.asyncio
async def test_skill_execution():
    executor = SkillExecutor(...)

    result = await executor.execute("my-skill", param1="test")

    assert result.success == True
```

## Troubleshooting

### Skill Not Found

```
Error: Skill not found and auto-install disabled: my-skill
```

**Solution**: Enable auto-install or manually install the skill.

### Installation Failed

```
Error: Failed to install skill: my-skill
```

**Solutions**:
1. Check network connectivity
2. Verify repository URL in skill.yaml
3. Check Python version compatibility
4. Install dependencies manually

### Execution Failed

```
Error: Missing required parameters: ['param1']
```

**Solution**: Provide all required parameters as defined in skill schema.

## Future Enhancements

### Planned Features

1. **Sandboxed Execution** - Run skills in isolated environments
2. **Permission System** - Fine-grained control over skill capabilities
3. **Skill Versioning** - Support multiple versions of the same skill
4. **Skill Marketplace UI** - Web interface for browsing skills
5. **Skill Analytics** - Usage tracking and performance metrics
6. **Skill Dependencies** - Skills that depend on other skills
7. **Skill Composition** - Combine multiple skills into workflows

## API Reference

### AgentSkill

```python
class AgentSkill(ABC):
    async def initialize(self) -> bool
    async def execute(self, **kwargs) -> SkillResult
    async def cleanup(self)
    def get_schema(self) -> Dict[str, Any]
    def validate_params(self, required: List[str], provided: Dict[str, Any])
```

### SkillMetadata

```python
@dataclass
class SkillMetadata:
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    dependencies: List[str]
    python_version: str
    homepage: Optional[str]
    repository: Optional[str]
    license: Optional[str]
```

### SkillResult

```python
@dataclass
class SkillResult:
    success: bool
    output: Any
    error: Optional[str]
    metadata: Dict[str, Any]
    execution_time: float
```

### SkillRegistry

```python
class SkillRegistry:
    async def register(self, skill: AgentSkill, initialize: bool = True) -> bool
    async def unregister(self, skill_name: str)
    def get_skill(self, skill_name: str) -> Optional[AgentSkill]
    def list_skills(self) -> List[Dict[str, str]]
    async def execute_skill(self, skill_name: str, **kwargs) -> SkillResult
    async def cleanup_all()
```

### SkillMarketplace

```python
class SkillMarketplace:
    def add_source(self, source: str)
    def remove_source(self, source: str)
    async def search(self, query: str, category: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 10) -> List[SkillMetadata]
    async def get_skill_info(self, skill_name: str) -> Optional[SkillMetadata]
    async def download_skill(self, skill_name: str, target_dir: Path, version: Optional[str] = None) -> Optional[Path]
    def clear_cache()
```

### SkillInstaller

```python
class SkillInstaller:
    async def install(self, skill_dir: Path, install_deps: bool = True) -> Optional[AgentSkill]
    async def uninstall(self, skill_dir: Path)
```

### SkillExecutor

```python
class SkillExecutor:
    async def execute(self, skill_name: str, timeout: Optional[int] = None, sandbox: bool = False, **kwargs) -> SkillResult
    async def discover_skills(self, query: str, category: Optional[str] = None, tags: Optional[list] = None) -> list
    def list_installed_skills(self) -> list
```

## Examples

See `examples/skills/example-skill/` for a complete working example.

## License

MIT
