# Self-Improvement Loop Infrastructure - Architecture Documentation

## Overview

The Self-Improvement Loop Infrastructure (Phase 5.1) enables Alpha to learn from its execution history and automatically improve its performance over time. The system analyzes logs, identifies patterns, generates improvement recommendations, and applies changes to the system configuration.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Feedback Loop                            │
│  ┌────────────┐   ┌───────────────┐   ┌─────────────────┐  │
│  │ Scheduler  │──▶│ Orchestrator  │──▶│ Metrics Tracker │  │
│  └────────────┘   └───────┬───────┘   └─────────────────┘  │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Log Analyzer │ │  Improvement │ │  Learning    │
    │              │ │   Executor   │ │    Store     │
    │ - Pattern    │ │ - Apply      │ │ - Patterns   │
    │   Detection  │ │   Changes    │ │ - Metrics    │
    │ - Recommend  │ │ - Validate   │ │ - Improve-   │
    │   Generation │ │ - Rollback   │ │   ments      │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           ▼                ▼                ▼
    ┌──────────────────────────────────────────────┐
    │           Execution Logs (JSON)              │
    │           Config Files (YAML)                │
    │           Learning Database (SQLite)         │
    └──────────────────────────────────────────────┘
```

## Components

### 1. LogAnalyzer (`alpha/learning/log_analyzer.py`)

**Purpose:** Analyze execution logs to identify patterns and inefficiencies.

**Key Features:**
- Pattern detection (errors, slow operations, timeouts, high costs)
- Time-based analysis (last day/week/month)
- Recommendation generation with priority scoring
- Success pattern identification

**Pattern Types:**
- `RECURRING_ERROR` - Errors that happen repeatedly
- `SLOW_OPERATION` - Operations consistently taking too long
- `INEFFICIENT_CHAIN` - Tool usage patterns that could be optimized
- `HIGH_COST_OPERATION` - LLM operations with high costs
- `SUCCESSFUL_PATTERN` - Patterns with high success rates
- `TIMEOUT_PATTERN` - Operations that frequently timeout

**Key Methods:**
```python
async def analyze_logs(time_range, log_files) -> List[LogPattern]
async def generate_recommendations(patterns) -> List[ImprovementRecommendation]
async def analyze_time_period(days) -> Dict[str, Any]
```

**Configuration:**
```python
min_error_occurrences = 3  # Minimum occurrences to be considered a pattern
slow_operation_threshold = 5.0  # seconds
high_cost_threshold = 0.10  # USD
timeout_threshold = 30.0  # seconds
```

### 2. ImprovementExecutor (`alpha/learning/improvement_executor.py`)

**Purpose:** Apply improvement recommendations to system configuration.

**Key Features:**
- Configuration file updates (config.yaml modifications)
- Model routing adjustments
- Tool selection strategy changes
- Validation before applying
- Rollback capability
- Change tracking

**Action Types:**
- `config_update` - Modify configuration values (timeouts, limits, etc.)
- `model_routing` - Adjust model selection strategies
- `tool_strategy` - Change tool usage patterns
- `error_handling` - Improve error handling approaches

**Key Methods:**
```python
async def apply_recommendation(recommendation, validate, dry_run) -> AppliedImprovement
async def rollback_improvement(improvement_id) -> bool
async def get_applied_improvements(status) -> List[AppliedImprovement]
```

**Safety Features:**
- Validation before application
- Dry-run mode for testing
- Configuration backup
- Rollback support

### 3. LearningStore (`alpha/learning/learning_store.py`)

**Purpose:** Persistent storage for all learning data using SQLite.

**Database Schema:**

```sql
-- Detected patterns
CREATE TABLE patterns_detected (
    id INTEGER PRIMARY KEY,
    pattern_id TEXT UNIQUE,
    pattern_type TEXT,
    description TEXT,
    occurrences INTEGER,
    impact_score REAL,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    examples TEXT,
    metadata TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Applied improvements
CREATE TABLE improvements_applied (
    id INTEGER PRIMARY KEY,
    improvement_id TEXT UNIQUE,
    recommendation_title TEXT,
    action_type TEXT,
    changes TEXT,
    status TEXT,
    applied_at TIMESTAMP,
    rolled_back_at TIMESTAMP,
    error TEXT,
    metadata TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Success metrics
CREATE TABLE success_metrics (
    id INTEGER PRIMARY KEY,
    metric_type TEXT,
    metric_name TEXT,
    value REAL,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    metadata TEXT,
    created_at TIMESTAMP
);

-- Correlations
CREATE TABLE correlations (
    id INTEGER PRIMARY KEY,
    correlation_type TEXT,
    entity_a TEXT,
    entity_b TEXT,
    correlation_score REAL,
    sample_size INTEGER,
    metadata TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Key Methods:**
```python
async def store_pattern(pattern) -> str
async def store_improvement(improvement) -> str
async def store_metric(metric_type, metric_name, value, ...) -> int
async def store_correlation(correlation_type, entity_a, entity_b, ...) -> int
def get_patterns(pattern_type, min_impact, limit) -> List[Dict]
def get_improvements(status, action_type, limit) -> List[Dict]
```

### 4. FeedbackLoop (`alpha/learning/feedback_loop.py`)

**Purpose:** Orchestrate the continuous learning cycle.

**Learning Cycle:**
```
1. Analyze Logs
   ↓
2. Detect Patterns
   ↓
3. Generate Recommendations
   ↓
4. Filter by Confidence
   ↓
5. Apply Improvements
   ↓
6. Track Results
   ↓
7. Store Metrics
   ↓
[Repeat on Schedule]
```

**Operation Modes:**
- `MANUAL` - All improvements require manual approval
- `SEMI_AUTO` - Safe improvements auto-applied, risky ones require approval
- `FULL_AUTO` - All improvements auto-applied (with validation)

**Key Configuration:**
```python
@dataclass
class FeedbackLoopConfig:
    mode: FeedbackLoopMode = SEMI_AUTO
    analysis_frequency: str = "daily"  # daily, weekly, custom_cron
    analysis_days: int = 7
    min_confidence: float = 0.7
    max_daily_improvements: int = 5
    enable_rollback: bool = True
    dry_run_first: bool = True
```

**Key Methods:**
```python
async def start()  # Start the feedback loop
async def stop()  # Stop the feedback loop
async def run_cycle() -> Dict[str, Any]  # Run single learning cycle
async def manual_trigger() -> Dict[str, Any]  # Manually trigger cycle
async def rollback_last_improvement() -> bool
```

## Data Flow

### 1. Log Analysis Flow

```
Execution Logs
    │
    ├─▶ [Load Logs] ─▶ [Filter by Time Range]
    │
    ├─▶ [Detect Errors] ─▶ Error Patterns
    │
    ├─▶ [Detect Slow Ops] ─▶ Performance Patterns
    │
    ├─▶ [Detect Costs] ─▶ Cost Patterns
    │
    └─▶ [Detect Success] ─▶ Success Patterns
```

### 2. Improvement Application Flow

```
Recommendation
    │
    ├─▶ [Validate] ─▶ Check Confidence
    │                 Check Action Type
    │                 Check Prerequisites
    │
    ├─▶ [Dry Run] ─▶ Simulate Changes
    │                Test Safety
    │
    ├─▶ [Backup] ─▶ Save Current Config
    │
    ├─▶ [Apply] ─▶ Update Configuration
    │              Modify Settings
    │              Save Changes
    │
    └─▶ [Track] ─▶ Store in Learning DB
                   Log Application
                   Monitor Results
```

### 3. Feedback Loop Cycle

```
[Scheduled Trigger]
    │
    ▼
[Analyze Logs for Period]
    │
    ├─▶ Patterns Found
    │
    ▼
[Generate Recommendations]
    │
    ├─▶ Recommendations Created
    │
    ▼
[Filter by Confidence]
    │
    ├─▶ High-Confidence Recs
    │
    ▼
[Apply Improvements]
    │
    ├─▶ Safe Actions (Auto)
    ├─▶ Risky Actions (Manual)
    │
    ▼
[Track Metrics]
    │
    ├─▶ Success Rates
    ├─▶ Impact Measures
    │
    ▼
[Store Results in DB]
```

## Integration with Existing Systems

### 1. Monitoring System Integration

```python
from alpha.monitoring import ExecutionLogger

# ExecutionLogger already logs to JSON files
# LogAnalyzer reads these files directly
analyzer = LogAnalyzer(log_dir="logs")
patterns = await analyzer.analyze_logs()
```

### 2. Scheduler Integration

```python
from alpha.scheduler import TaskScheduler, ScheduleConfig, ScheduleType

# Register feedback loop executor
scheduler.register_executor("feedback_loop_executor", feedback_loop.run_cycle)

# Schedule daily analysis
schedule_config = ScheduleConfig(
    type=ScheduleType.DAILY,
    time="02:00"
)

await scheduler.schedule_task(task_spec, schedule_config)
```

### 3. Configuration System Integration

```python
# ImprovementExecutor reads and writes config.yaml
executor = ImprovementExecutor(config_path="config.yaml")

# Changes are applied directly to configuration
await executor.apply_recommendation(recommendation)

# Config updates take effect on next system restart
# or can be hot-reloaded by specific components
```

## Usage Examples

### Basic Usage

```python
from alpha.learning import (
    LogAnalyzer,
    ImprovementExecutor,
    LearningStore,
    FeedbackLoop,
    FeedbackLoopConfig,
    FeedbackLoopMode
)

# Initialize components
log_analyzer = LogAnalyzer(log_dir="logs")
improvement_executor = ImprovementExecutor(config_path="config.yaml")
learning_store = LearningStore(db_path="data/learning.db")
learning_store.initialize()

# Link executor to store
improvement_executor.learning_store = learning_store

# Configure feedback loop
config = FeedbackLoopConfig(
    mode=FeedbackLoopMode.SEMI_AUTO,
    analysis_frequency="daily",
    analysis_days=7,
    min_confidence=0.7,
    max_daily_improvements=5
)

# Create feedback loop
feedback_loop = FeedbackLoop(
    config=config,
    log_analyzer=log_analyzer,
    improvement_executor=improvement_executor,
    learning_store=learning_store
)

# Start the loop
await feedback_loop.start()

# Run a cycle manually
result = await feedback_loop.manual_trigger()
print(f"Patterns found: {result['steps']['analysis']['patterns_found']}")
print(f"Improvements applied: {result['steps']['improvements']['applied']}")
```

### Manual Analysis

```python
# Analyze logs for last 7 days
analyzer = LogAnalyzer(log_dir="logs")
analysis = await analyzer.analyze_time_period(days=7)

print(f"Patterns: {analysis['patterns']['total']}")
print(f"Top patterns:")
for pattern in analysis['top_patterns']:
    print(f"  - {pattern['description']} ({pattern['occurrences']}x)")

print(f"\nTop recommendations:")
for rec in analysis['top_recommendations']:
    print(f"  - {rec['title']} (priority: {rec['priority']})")
```

### Direct Improvement Application

```python
# Generate and apply improvements
analyzer = LogAnalyzer(log_dir="logs")
executor = ImprovementExecutor(config_path="config.yaml")

# Analyze
patterns = await analyzer.analyze_logs()
recommendations = await analyzer.generate_recommendations()

# Apply high-priority recommendations
for rec in recommendations:
    if rec.priority.value >= 4:  # HIGH or CRITICAL
        # Test with dry run first
        result = await executor.apply_recommendation(rec, dry_run=True)

        if result.status != ImprovementStatus.FAILED:
            # Apply for real
            result = await executor.apply_recommendation(rec, dry_run=False)
            print(f"Applied: {rec.title}")
```

## Performance Considerations

### 1. Log Processing
- Logs are read line-by-line (streaming)
- Time-range filtering reduces memory usage
- Pattern detection uses efficient data structures (Counter, defaultdict)

### 2. Database Storage
- SQLite with indexes for fast queries
- JSON fields for flexible metadata
- Regular cleanup of old data recommended

### 3. Improvement Application
- Validation before applying (prevents invalid changes)
- Dry-run mode for testing (no side effects)
- Rollback capability (safety net)

## Security Considerations

### 1. Configuration Changes
- All changes are validated before applying
- Backup created before modifications
- Rollback available for all changes
- Audit trail in learning database

### 2. Recommendation Filtering
- Confidence threshold prevents low-quality changes
- Action type filtering (safe vs. risky)
- Daily quota limits blast radius
- Manual approval for risky changes

### 3. Database Access
- SQLite file permissions should be restricted
- No SQL injection (parameterized queries)
- Connection pooling disabled (check_same_thread=False for async)

## Monitoring and Debugging

### 1. Logging
All components use structured logging:
```python
logger.info(f"Detected {len(patterns)} patterns")
logger.error(f"Failed to apply improvement: {e}", exc_info=True)
```

### 2. Statistics
Get system statistics:
```python
# Feedback loop stats
stats = feedback_loop.get_statistics()

# Learning store stats
db_stats = learning_store.get_statistics()

# Executor stats
exec_stats = executor.get_statistics()
```

### 3. Status Checking
```python
# Check feedback loop status
status = feedback_loop.get_status()
print(f"Running: {status['running']}")
print(f"Cycles completed: {status['cycle_count']}")
print(f"Last cycle: {status['last_cycle']}")
```

## Testing

Comprehensive test suite in `tests/learning/`:
- `test_log_analyzer.py` - Pattern detection and recommendation generation (15 tests)
- `test_improvement_executor.py` - Improvement application and rollback (12 tests)
- `test_learning_store.py` - Database operations (18 tests)
- `test_feedback_loop.py` - Orchestration and cycles (13 tests)
- `test_integration.py` - End-to-end integration (8 tests)

**Total: 66 tests**

Run tests:
```bash
pytest tests/learning/ -v
```

## Future Enhancements

### Phase 5.2 - Proactive Intelligence
- Predictive analytics (forecast issues before they occur)
- Anomaly detection
- Trend analysis

### Phase 5.3 - Skill Evolution
- Automatic skill improvement
- Skill performance tracking
- Skill recommendation based on usage patterns

### Additional Features
- A/B testing for improvements
- Multi-objective optimization
- Distributed learning (learn from multiple Alpha instances)
- ML-based pattern detection
- Natural language explanations for improvements

## Conclusion

The Self-Improvement Loop Infrastructure provides Alpha with the ability to learn from its execution history and continuously improve its performance. The system is designed to be safe, reliable, and extensible, with comprehensive testing and monitoring capabilities.
