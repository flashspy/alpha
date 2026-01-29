# Agent Skill System - Quick Start Guide

## What are Agent Skills?

Agent Skills are **dynamic, installable capabilities** that extend Alpha's functionality beyond built-in tools. They can be:

- 🔍 **Auto-discovered** from skill repositories
- 📦 **Auto-installed** when needed
- ♻️ **Reusable** across different tasks
- 📚 **Versioned** for compatibility
- 🔐 **Sandboxed** for security (coming soon)

## Quick Start (5 minutes)

### 1. Start Alpha

```bash
./start.sh
```

### 2. Check Available Skills

```
You: skills
```

Alpha will show you installed skills. Initially, the list will be empty.

### 3. Use a Skill (Auto-Install)

Just use it naturally - Alpha will find and install it automatically:

```
You: Convert "hello world" to uppercase using a skill

Alpha: I'll use the example-skill for this.

[Auto-installing example-skill...]

Result: "HELLO WORLD"
```

### 4. Search for Skills

```
You: search skill text
```

Alpha will show available skills related to text processing.

### 5. Create Your Own Skill (Optional)

Copy the example skill and customize it:

```bash
cp -r examples/skills/example-skill ~/.alpha/local_skills/my-skill
cd ~/.alpha/local_skills/my-skill

# Edit skill.yaml and skill.py
nano skill.yaml
nano skill.py
```

## Example: Creating a Simple Skill

### Step 1: Create Directory Structure

```bash
mkdir -p ~/.alpha/local_skills/greeting-skill
cd ~/.alpha/local_skills/greeting-skill
```

### Step 2: Create skill.yaml

```yaml
name: greeting-skill
version: "1.0.0"
description: "Generate personalized greetings"
author: "Your Name"
category: "utility"
tags:
  - greeting
  - text
dependencies: []
python_version: ">=3.8"
```

### Step 3: Create skill.py

```python
from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult

class GreetingSkill(AgentSkill):
    """Generate personalized greetings."""

    async def initialize(self) -> bool:
        return True

    async def execute(self, name: str, style: str = "formal", **kwargs) -> SkillResult:
        """
        Generate a greeting.

        Args:
            name: Person's name
            style: Greeting style (formal, casual, friendly)
        """
        greetings = {
            "formal": f"Good day, {name}. It is a pleasure to meet you.",
            "casual": f"Hey {name}, what's up?",
            "friendly": f"Hello {name}! Great to see you!"
        }

        greeting = greetings.get(style, greetings["formal"])

        return SkillResult(
            success=True,
            output={"greeting": greeting, "name": name, "style": style}
        )

    async def cleanup(self):
        pass
```

### Step 4: Use Your Skill

```
You: Create a friendly greeting for Alice

Alpha: SKILL: greeting-skill
PARAMS:
  name: "Alice"
  style: "friendly"

Result: "Hello Alice! Great to see you!"
```

## Common Use Cases

### 1. Text Processing

```
You: Reverse the text "hello world"
→ Alpha uses text-processing skill
→ Result: "dlrow olleh"
```

### 2. Data Analysis

```
You: Calculate statistics for [1, 2, 3, 4, 5]
→ Alpha uses stats-skill
→ Result: {"mean": 3, "median": 3, "std": 1.41}
```

### 3. Image Processing

```
You: Resize image.jpg to 800x600
→ Alpha uses image-processing skill
→ Result: Resized image saved
```

## Skill vs Tool - When to Use Which?

### Use Built-in Tools When:
- ✅ Built-in capability (shell, file, http, search)
- ✅ Simple, single operation
- ✅ No external dependencies

### Use Skills When:
- ✅ Complex, specialized functionality
- ✅ Requires external libraries
- ✅ Reusable across projects
- ✅ Community-contributed capability

## Tips & Best Practices

### 1. Skill Discovery

```
# Search by keyword
search skill image

# Search by category
search skill ai

# List installed
skills
```

### 2. Error Handling

If auto-install fails:
```
# Check network connection
# Verify repository URL
# Install dependencies manually
cd ~/.alpha/skills/skill-name
pip install -r requirements.txt
```

### 3. Skill Updates

Skills are cached. To force refresh:
```python
# In Python
marketplace.clear_cache()
```

### 4. Local Development

Test your skill before publishing:
```bash
# Install locally
cp -r my-skill ~/.alpha/local_skills/

# Test in Alpha
You: Use my-skill with param1="test"
```

## Next Steps

1. 📖 Read the full documentation: `docs/AGENT_SKILLS.md`
2. 🔍 Explore example skills: `examples/skills/`
3. 🧪 Run tests: `python tests/test_agent_skills.py`
4. 🚀 Create your own skill following the structure above
5. 📦 Share your skills with the community

## Troubleshooting

### Problem: "Skill not found"

**Cause**: Skill not in marketplace or auto-install disabled

**Solution**:
```bash
# Enable auto-install (default)
# OR manually install
cd ~/.alpha/skills
git clone https://github.com/user/skill-name
```

### Problem: "Import error" when using skill

**Cause**: Missing dependencies

**Solution**:
```bash
cd ~/.alpha/skills/skill-name
pip install -r requirements.txt
```

### Problem: Skill execution timeout

**Cause**: Long-running operation

**Solution**: Increase timeout in skill call
```python
result = await executor.execute("my-skill", timeout=60, ...)
```

## Getting Help

- 📧 Report issues: https://github.com/alpha-ai/alpha/issues
- 💬 Community: https://github.com/alpha-ai/alpha/discussions
- 📚 Docs: `docs/AGENT_SKILLS.md`

## What's Next?

The Agent Skill system is continuously evolving. Upcoming features:

- 🔐 **Sandboxed Execution** - Enhanced security
- 🎯 **Permission System** - Fine-grained control
- 🌐 **Skill Marketplace UI** - Visual browsing
- 📊 **Analytics** - Usage tracking
- 🔗 **Skill Composition** - Combine skills into workflows

Start creating your skills today! 🚀
