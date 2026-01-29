# Alpha Tools Expansion - Specification

## Requirement ID: REQ-025
**Feature**: Practical Tools Expansion
**Priority**: High
**Estimated Effort**: 2-3 days
**Version**: v0.2.0

## Overview

Expand Alpha's tool system with practical, frequently-used tools to enhance daily task handling capabilities.

## New Tools Specification

### 1. HTTPTool

**Purpose**: Execute HTTP requests for API calls and web content fetching

**Operations**:
- `GET`: Retrieve data from URL
- `POST`: Submit data to API
- `PUT`: Update resource
- `DELETE`: Delete resource
- `PATCH`: Partial update

**Parameters**:
- `url` (required): Target URL
- `method` (required): HTTP method
- `headers` (optional): Dict of headers
- `params` (optional): Query parameters
- `data` (optional): Request body for POST/PUT/PATCH
- `json` (optional): JSON body (auto sets Content-Type)
- `timeout` (optional): Request timeout (default: 30s)
- `follow_redirects` (optional): Follow redirects (default: True)

**Returns**:
- `status_code`: HTTP status code
- `headers`: Response headers
- `body`: Response body (text)
- `json`: Parsed JSON if applicable
- `elapsed`: Request duration

**Error Handling**:
- Network errors
- Timeout errors
- Invalid URL
- HTTP error status (4xx, 5xx)

**Security**:
- URL validation
- No credential logging
- HTTPS preferred warning

### 2. DateTimeTool

**Purpose**: Date and time operations, timezone handling

**Operations**:
- `now`: Get current datetime
- `format`: Format datetime string
- `parse`: Parse datetime string
- `add`: Add duration to datetime
- `subtract`: Subtract duration from datetime
- `diff`: Calculate difference between two datetimes
- `timezone_convert`: Convert between timezones

**Parameters**:
- `operation` (required): Operation type
- `datetime` (optional): Datetime string (ISO 8601)
- `format` (optional): Format string
- `timezone` (optional): Timezone name (e.g., "Asia/Shanghai", "UTC")
- `duration` (optional): Duration dict {days, hours, minutes, seconds}
- `datetime1`, `datetime2` (optional): For diff operation

**Returns**:
- Operation-specific result (datetime string, duration, etc.)

**Supported Formats**:
- ISO 8601 (default)
- RFC 3339
- Custom strftime formats

**Timezone Support**:
- IANA timezone database
- UTC offset notation

### 3. CalculatorTool

**Purpose**: Safe mathematical expression evaluation and calculations

**Operations**:
- `calculate`: Evaluate mathematical expression
- `convert_unit`: Unit conversion

**Parameters**:
- `operation` (required): Operation type
- `expression` (optional): Math expression string
- `value` (optional): Numeric value for conversion
- `from_unit` (optional): Source unit
- `to_unit` (optional): Target unit

**Supported Operations**:
- Basic arithmetic: +, -, *, /, //, %, **
- Functions: sqrt, sin, cos, tan, log, ln, exp, abs, round, floor, ceil
- Constants: pi, e

**Unit Conversions**:
- Length: m, km, mi, ft, in, cm, mm
- Weight: kg, g, mg, lb, oz
- Temperature: C, F, K
- Time: s, min, h, day
- Data: B, KB, MB, GB, TB

**Security**:
- Sandboxed evaluation (no code execution)
- Expression validation
- Whitelist of allowed functions

### 4. SearchTool Enhancement

**Purpose**: Real web search capability

**Implementation Options**:
1. **SerpAPI** (Recommended)
   - Simple API
   - Good free tier
   - Multiple search engines

2. **DuckDuckGo API**
   - Free
   - No API key required
   - Privacy-focused

3. **Google Custom Search API**
   - High quality
   - Limited free quota
   - Requires API key

**Decision**: Start with DuckDuckGo (no API key), support SerpAPI as optional

**Parameters**:
- `query` (required): Search query
- `limit` (optional): Max results (default: 5, max: 20)
- `safe_search` (optional): Safe search level
- `region` (optional): Search region

**Returns**:
- List of results:
  - `title`: Page title
  - `url`: Page URL
  - `snippet`: Text snippet
  - `source`: Search engine used

## Implementation Plan

### Phase 1: HTTPTool (Day 1)
- [ ] Implement HTTPTool class
- [ ] Add to registry
- [ ] Unit tests
- [ ] Integration test with public API

### Phase 2: DateTimeTool (Day 1-2)
- [ ] Implement DateTimeTool class
- [ ] Timezone support with pytz
- [ ] Unit tests with various timezones
- [ ] Edge case testing

### Phase 3: CalculatorTool (Day 2)
- [ ] Implement safe expression evaluator
- [ ] Add unit conversion
- [ ] Security validation
- [ ] Comprehensive tests

### Phase 4: SearchTool Enhancement (Day 2-3)
- [ ] Integrate DuckDuckGo
- [ ] Fallback to placeholder
- [ ] Optional SerpAPI support
- [ ] Rate limiting
- [ ] Tests with mocked responses

### Phase 5: Integration & Documentation (Day 3)
- [ ] Update tool registry
- [ ] CLI integration testing
- [ ] Update user documentation
- [ ] Update internal documentation
- [ ] Create usage examples

## Dependencies

New packages required:
```
aiohttp>=3.9.0  # Already in requirements (for HTTPTool)
python-dateutil>=2.8.0  # Date parsing
pytz>=2024.1  # Timezone support
duckduckgo-search>=4.0.0  # DuckDuckGo API
```

Optional:
```
google-search-results>=2.4.0  # SerpAPI
```

## Testing Strategy

### Unit Tests
- Each tool in isolation
- Parameter validation
- Error handling
- Edge cases

### Integration Tests
- Tools working with LLM
- CLI interaction
- Real API calls (with mocks available)

### Security Tests
- CalculatorTool expression injection
- HTTPTool SSRF prevention
- Input sanitization

## Success Criteria

- [ ] All 4 tools implemented and registered
- [ ] Test coverage > 85%
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Successfully used in CLI session

## Risks and Mitigations

**Risk**: External API dependencies
**Mitigation**: Graceful fallback, error handling

**Risk**: Security in CalculatorTool
**Mitigation**: Sandboxed evaluation, whitelist approach

**Risk**: Timezone complexity
**Mitigation**: Use established library (pytz), comprehensive tests

## Deliverables

1. Updated `alpha/tools/registry.py` with new tools
2. Test file `tests/test_tools_expansion.py`
3. Updated `docs/en/features.md` and `docs/zh/features.md`
4. Updated `requirements.txt`
5. This specification document
6. Test report document

---

**Status**: In Progress
**Created**: 2026-01-29
**Author**: Claude (AI Development Assistant)
