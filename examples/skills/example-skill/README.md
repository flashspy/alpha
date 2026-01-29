# Example Skill

This is an example skill that demonstrates how to create and use Agent Skills in Alpha.

## Features

- Text transformation (uppercase, lowercase, reverse)
- Character counting
- Word counting

## Usage

### Uppercase
```
SKILL: example-skill
PARAMS:
  operation: "uppercase"
  text: "hello world"
```

### Count Words
```
SKILL: example-skill
PARAMS:
  operation: "count_words"
  text: "hello world from alpha"
```

## Installation

This skill will be automatically discovered and installed when you use it in Alpha.

## Development

To create your own skill based on this example:

1. Copy this directory structure
2. Update `skill.yaml` with your skill's metadata
3. Implement your skill logic in `skill.py`
4. Test your skill

## License

MIT
