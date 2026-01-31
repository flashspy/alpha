"""
LLM Prompt Templates for Task Decomposition (REQ-8.1)

Defines prompt templates for:
- Task complexity analysis
- Task decomposition into hierarchical sub-tasks
- Adaptive re-decomposition based on intermediate results
"""

# Task Analysis Prompt
TASK_ANALYSIS_PROMPT = """You are a task analysis expert. Analyze the following user request and classify its complexity.

**User Request:**
{user_request}

**Available Tools/Capabilities:**
{available_tools}

**Context:**
{context}

**Your Task:**
1. Classify the complexity level (simple, medium, complex, expert)
2. Estimate total execution time
3. Determine if task decomposition is needed
4. List required capabilities/tools

**Guidelines:**
- SIMPLE: 1-2 steps, <1min (e.g., "What is 5+3?", "Check current time")
- MEDIUM: 3-5 steps, 1-10min (e.g., "Search web and summarize", "Analyze a CSV file")
- COMPLEX: 6-15 steps, 10-60min (e.g., "Implement user auth system", "Generate report with visualizations")
- EXPERT: 15+ steps, >60min (e.g., "Build full REST API", "Migrate database schema")

**Decomposition Criteria:**
- Decompose if: complexity >= COMPLEX OR steps >= 6 OR duration > 10min
- Don't decompose if: single-step task OR simple calculation OR basic Q&A

**Output Format (JSON):**
```json
{{
  "complexity_level": "simple|medium|complex|expert",
  "estimated_duration": <seconds>,
  "decomposition_needed": true|false,
  "required_capabilities": ["tool1", "tool2"],
  "reasoning": "Brief explanation of analysis"
}}
```

Analyze now:"""


# Task Decomposition Prompt
TASK_DECOMPOSITION_PROMPT = """You are a task decomposition expert. Break down the complex user request into a hierarchical tree of manageable sub-tasks.

**User Request:**
{user_request}

**Complexity Analysis:**
- Level: {complexity_level}
- Estimated Duration: {estimated_duration}s
- Required Capabilities: {required_capabilities}

**Available Tools:**
{available_tools}

**Project Context:**
{project_context}

**Decomposition Guidelines:**

1. **Create 3-7 main phases** (top-level tasks)
   - Each phase represents a major step toward the goal
   - Phases should be logically sequential

2. **Break each phase into 2-5 specific sub-tasks**
   - Sub-tasks should be atomic (1-5 min execution)
   - Each sub-task should have clear deliverables

3. **Identify dependencies**
   - List task IDs that must complete before each task
   - Use hierarchical IDs (e.g., "1", "1.1", "1.2", "2", "2.1")

4. **Estimate durations** (in seconds)
   - Be realistic based on task complexity
   - Account for potential errors/retries

5. **Parallel execution opportunities**
   - Mark independent tasks that can run in parallel
   - Specify execution strategy (sequential/parallel/hybrid)

**Output Format (JSON):**
```json
{{
  "root_task": {{
    "id": "0",
    "description": "<overall goal summary>",
    "estimated_duration": <total seconds>
  }},
  "phases": [
    {{
      "id": "1",
      "description": "<phase 1 description>",
      "parent_id": "0",
      "depth": 1,
      "dependencies": [],
      "estimated_duration": <seconds>,
      "sub_tasks": [
        {{
          "id": "1.1",
          "description": "<specific task>",
          "parent_id": "1",
          "depth": 2,
          "dependencies": [],
          "estimated_duration": <seconds>
        }},
        {{
          "id": "1.2",
          "description": "<specific task>",
          "parent_id": "1",
          "depth": 2,
          "dependencies": ["1.1"],
          "estimated_duration": <seconds>
        }}
      ]
    }},
    {{
      "id": "2",
      "description": "<phase 2 description>",
      "parent_id": "0",
      "depth": 1,
      "dependencies": ["1"],
      "estimated_duration": <seconds>,
      "sub_tasks": [...]
    }}
  ],
  "execution_strategy": "sequential|parallel|hybrid",
  "reasoning": "Brief explanation of decomposition approach"
}}
```

**Example (Software Development Task):**

User Request: "Implement user authentication with JWT tokens"

Output:
```json
{{
  "root_task": {{
    "id": "0",
    "description": "Implement JWT-based user authentication system",
    "estimated_duration": 1800
  }},
  "phases": [
    {{
      "id": "1",
      "description": "Analyze current codebase structure",
      "parent_id": "0",
      "depth": 1,
      "dependencies": [],
      "estimated_duration": 120,
      "sub_tasks": [
        {{
          "id": "1.1",
          "description": "Check existing authentication code",
          "parent_id": "1",
          "depth": 2,
          "dependencies": [],
          "estimated_duration": 60
        }},
        {{
          "id": "1.2",
          "description": "Identify framework and dependencies",
          "parent_id": "1",
          "depth": 2,
          "dependencies": ["1.1"],
          "estimated_duration": 60
        }}
      ]
    }},
    {{
      "id": "2",
      "description": "Design authentication architecture",
      "parent_id": "0",
      "depth": 1,
      "dependencies": ["1"],
      "estimated_duration": 300,
      "sub_tasks": [
        {{
          "id": "2.1",
          "description": "Define JWT token structure and claims",
          "parent_id": "2",
          "depth": 2,
          "dependencies": [],
          "estimated_duration": 120
        }},
        {{
          "id": "2.2",
          "description": "Design refresh token strategy",
          "parent_id": "2",
          "depth": 2,
          "dependencies": ["2.1"],
          "estimated_duration": 180
        }}
      ]
    }},
    {{
      "id": "3",
      "description": "Implement JWT token generation and validation",
      "parent_id": "0",
      "depth": 1,
      "dependencies": ["2"],
      "estimated_duration": 600,
      "sub_tasks": [
        {{
          "id": "3.1",
          "description": "Install JWT library (jsonwebtoken)",
          "parent_id": "3",
          "depth": 2,
          "dependencies": [],
          "estimated_duration": 60
        }},
        {{
          "id": "3.2",
          "description": "Create token generation utility function",
          "parent_id": "3",
          "depth": 2,
          "dependencies": ["3.1"],
          "estimated_duration": 240
        }},
        {{
          "id": "3.3",
          "description": "Create token validation middleware",
          "parent_id": "3",
          "depth": 2,
          "dependencies": ["3.2"],
          "estimated_duration": 240
        }},
        {{
          "id": "3.4",
          "description": "Add unit tests for token utilities",
          "parent_id": "3",
          "depth": 2,
          "dependencies": ["3.2", "3.3"],
          "estimated_duration": 180
        }}
      ]
    }},
    {{
      "id": "4",
      "description": "Implement authentication endpoints",
      "parent_id": "0",
      "depth": 1,
      "dependencies": ["3"],
      "estimated_duration": 480,
      "sub_tasks": [...]
    }},
    {{
      "id": "5",
      "description": "Integration testing and documentation",
      "parent_id": "0",
      "depth": 1,
      "dependencies": ["4"],
      "estimated_duration": 300,
      "sub_tasks": [...]
    }}
  ]],
  "execution_strategy": "sequential",
  "reasoning": "Authentication requires sequential implementation: analyze → design → implement → test. Sub-tasks within phases can run in parallel where dependencies allow."
}}
```

Now decompose the user's request:"""


# Re-decomposition Prompt (Adaptive Adjustment)
REDECOMPOSITION_PROMPT = """You are a task decomposition expert. Adjust the task decomposition based on intermediate execution results.

**Original User Request:**
{user_request}

**Current Task Tree:**
{current_tree}

**Execution Results So Far:**
{execution_results}

**Completed Tasks:**
{completed_tasks}

**Your Task:**
Analyze the results and determine if the remaining tasks need adjustment:

1. **Success Case**: If results indicate easier/faster path → simplify remaining tasks
2. **Complexity Case**: If results reveal more work needed → add sub-tasks
3. **Blocker Case**: If results show dependency issue → reorder or add prerequisite tasks
4. **Alternative Path**: If current approach not working → suggest different strategy

**Output Format (JSON):**
```json
{{
  "adjustment_needed": true|false,
  "reasoning": "Why adjustment is needed",
  "updated_tasks": [
    {{
      "id": "3",
      "action": "modify|add|remove|reorder",
      "new_description": "...",
      "new_dependencies": ["..."],
      "new_estimated_duration": <seconds>
    }}
  ],
  "new_tasks": [
    {{
      "id": "5.3",
      "description": "...",
      "parent_id": "5",
      "depth": 2,
      "dependencies": ["..."],
      "estimated_duration": <seconds>
    }}
  ]
}}
```

Analyze and adjust:"""


# Formatting instructions for consistent JSON output
JSON_FORMAT_INSTRUCTIONS = """
**CRITICAL: Output ONLY valid JSON. No markdown, no code blocks, no explanation outside JSON.**

Start your response with `{` and end with `}`.
"""
