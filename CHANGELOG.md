[English](#english) | [简体中文](#中文)

---

# <a name="english"></a>English

# Alpha Enhancement - v0.2.0

## Update Date
2026-01-29

## Major Changes

### 1. Enhanced Tool Call Parser - Multi-Format Support

**Problem Fixed:**
- Users were seeing internal tool call details (TOOL: and PARAMS: lines) in responses
- LLM used multi-line YAML format that wasn't recognized by the parser

**Solution:**
- ✅ Enhanced `_parse_tool_calls()` to support both JSON and YAML formats
- ✅ Enhanced `_extract_user_message()` to filter multi-line PARAMS blocks
- ✅ Updated system prompt to clarify tool call lines are invisible to users

**Supported Formats:**
```python
# Single-line JSON (original)
PARAMS: {"url": "https://example.com", "method": "GET"}

# Multi-line YAML (new)
PARAMS:
  url: "https://example.com"
  method: "GET"

# Complex nested YAML (new)
PARAMS:
  headers:
    Content-Type: "application/json"
  json:
    query: "test"
```

**User Experience:**
- Before: Users saw raw `TOOL:` and `PARAMS:` lines
- After: Complete technical detail hiding, pure natural language interaction

### 2. Universal Tool Design Philosophy

**Removed:**
- Specialized WeatherTool (decided against dedicated tools for each scenario)

**Philosophy:**
- ✅ Use generic tools (HTTP, Search) to handle all scenarios
- ✅ LLM autonomously combines tools to solve problems
- ✅ No code changes needed for new use cases

**Tool Usage Guide:**
- Created `docs/TOOL_USAGE_GUIDE.md` with examples:
  - Weather queries: `HTTP + wttr.in API`
  - Stock market: `Search for latest data`
  - News: `Search with time filters`
  - Currency rates: `HTTP + exchange rate APIs`

### 3. System Prompt Enhancements

**Added:**
- Tool usage strategies (weather, real-time data, APIs)
- Format flexibility explanation (JSON/YAML)
- Critical reminder: tool calls are invisible to users

### 4. Testing Improvements

**New Tests:**
- ✅ `tests/test_parser.py` - Parser unit tests (4 scenarios)
- ✅ `tests/test_weather_http.py` - Weather API integration test
- ✅ All 25 comprehensive tests pass (100%)

**Test Coverage:**
- Single-line JSON parsing
- Multi-line YAML parsing
- Mixed format parsing
- Complex nested structure parsing

### 5. Documentation

**New Documents:**
- `docs/TOOL_USAGE_GUIDE.md` - Complete tool usage guide
- `docs/PARSER_ENHANCEMENT.md` - Parser enhancement details

## Bug Fixes

- Fixed `KeyError: 'city'` in system prompt formatting
- Fixed tool call visibility issue in CLI output
- Fixed `StopIteration` error in streaming response (Rich library bug in Python 3.12)
- Improved search tool timeout handling and error messages
- Added network connectivity fallback strategies

## Breaking Changes

None - fully backward compatible

---

# Alpha Configuration Update - v0.1.1

## Update Content

This update adds enhanced support for the Anthropic API, providing more flexible configuration options.

## Major Changes

### 1. Changed Default Provider to Anthropic

- ✅ Use `anthropic` as the default LLM provider
- ✅ Upgraded default model to `claude-3-5-sonnet-20241022`
- ✅ Increased maximum tokens to 8192

### 2. Added Environment Variable Support

**ANTHROPIC_AUTH_TOKEN** (Recommended)
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

**ANTHROPIC_API_KEY** (Compatible)
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

**ANTHROPIC_BASE_URL** (Optional)
```bash
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 3. Environment Variable Fallback Mechanism

Configuration files now support environment variable fallback syntax:

```yaml
api_key: "${ANTHROPIC_AUTH_TOKEN:-${ANTHROPIC_API_KEY}}"
```

Resolution order:
1. Prioritize `ANTHROPIC_AUTH_TOKEN`
2. If not set, fallback to `ANTHROPIC_API_KEY`
3. If neither is set, return empty string

### 4. Base URL Support

AnthropicProvider now supports custom API endpoints:

```python
client = AsyncAnthropic(
    api_key=api_key,
    base_url=base_url  # If configured
)
```

This allows using:
- Self-hosted Anthropic-compatible API
- Enterprise internal proxy
- Testing environment endpoints

## Code Changes

### Modified Files

1. **config.example.yaml** & **config.yaml**
   - Changed default provider to anthropic
   - Added base_url configuration
   - Updated api_key with fallback syntax
   - Upgraded model and token limits

2. **alpha/utils/config.py**
   - Enhanced `_replace_env_vars()` function
   - Support for `${VAR1:-${VAR2}}` syntax
   - Support for `${VAR:-default}` syntax

3. **alpha/llm/service.py**
   - AnthropicProvider supports base_url parameter
   - Pass base_url in complete() and stream_complete()
   - from_config() method passes base_url to provider

### New Files

1. **docs/anthropic_config.md** - Complete Anthropic configuration guide
2. **tests/test_config.py** - Configuration loading tests
3. **start.sh** - Quick start script

## Usage Examples

### Quick Start

```bash
# Set API key
export ANTHROPIC_AUTH_TOKEN="sk-ant-..."

# Start Alpha
./start.sh
```

### Using Custom Endpoint

```bash
export ANTHROPIC_AUTH_TOKEN="your-token"
export ANTHROPIC_BASE_URL="https://api.your-company.com"
./start.sh
```

### Switching Back to OpenAI

Edit config.yaml:
```yaml
llm:
  default_provider: "openai"
```

Then set:
```bash
export OPENAI_API_KEY="sk-..."
./start.sh
```

## Testing

Run configuration tests:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

Test coverage:
- ✅ Configuration file loading
- ✅ ANTHROPIC_AUTH_TOKEN parsing
- ✅ Fallback to ANTHROPIC_API_KEY
- ✅ Base URL configuration
- ✅ Model and parameter validation

## Backward Compatibility

This update is fully backward compatible:
- ✅ Still supports `ANTHROPIC_API_KEY`
- ✅ OpenAI configuration unaffected
- ✅ Existing configuration files remain valid

If `ANTHROPIC_API_KEY` is already set, no changes are needed - the system will use it automatically.

## Upgrade Steps

### Upgrading from v0.1.0

1. Update configuration file:
```bash
cp config.yaml config.yaml.bak
cp config.example.yaml config.yaml
# Adjust configuration as needed
```

2. Set environment variables:
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

3. Test configuration:
```bash
PYTHONPATH=. python tests/test_config.py
```

4. Start Alpha:
```bash
./start.sh
```

## Documentation Updates

- ✅ README.md - Updated installation instructions
- ✅ docs/quickstart.md - Updated configuration steps
- ✅ docs/anthropic_config.md - New complete configuration guide
- ✅ Updated code comments

## Next Steps

Recommended future features:
- [ ] Support more environment variables (timeout, retry, etc.)
- [ ] Add configuration validation command
- [ ] Support configuration hot reload
- [ ] Add multi-profile support

---

**Version**: v0.1.1
**Release Date**: 2026-01-29
**Change Type**: Feature Enhancement
**Backward Compatible**: Yes

---

# <a name="中文"></a>简体中文

# Alpha Configuration Update - v0.1.1

## 更新内容

本次更新增加了对Anthropic API的增强支持,提供更灵活的配置方式。

## 主要变更

### 1. 默认Provider改为Anthropic

- ✅ 默认使用 `anthropic` 作为LLM provider
- ✅ 默认模型升级为 `claude-3-5-sonnet-20241022`
- ✅ 最大token数提升至 8192

### 2. 新增环境变量支持

**ANTHROPIC_AUTH_TOKEN** (推荐)
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

**ANTHROPIC_API_KEY** (兼容)
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

**ANTHROPIC_BASE_URL** (可选)
```bash
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 3. 环境变量Fallback机制

配置文件现在支持环境变量fallback语法:

```yaml
api_key: "${ANTHROPIC_AUTH_TOKEN:-${ANTHROPIC_API_KEY}}"
```

解析顺序:
1. 优先使用 `ANTHROPIC_AUTH_TOKEN`
2. 如果未设置,fallback到 `ANTHROPIC_API_KEY`
3. 如果都未设置,返回空字符串

### 4. Base URL支持

AnthropicProvider现在支持自定义API端点:

```python
client = AsyncAnthropic(
    api_key=api_key,
    base_url=base_url  # 如果设置的话
)
```

这允许使用:
- 自建Anthropic兼容API
- 企业内部代理
- 测试环境端点

## 代码变更

### 修改的文件

1. **config.example.yaml** & **config.yaml**
   - 默认provider改为anthropic
   - 添加base_url配置
   - 更新api_key为fallback语法
   - 升级模型和token限制

2. **alpha/utils/config.py**
   - 增强`_replace_env_vars()`函数
   - 支持`${VAR1:-${VAR2}}`语法
   - 支持`${VAR:-default}`语法

3. **alpha/llm/service.py**
   - AnthropicProvider支持base_url参数
   - 在complete()和stream_complete()中传递base_url
   - from_config()方法传递base_url到provider

### 新增文件

1. **docs/anthropic_config.md** - Anthropic配置完整指南
2. **tests/test_config.py** - 配置加载测试
3. **start.sh** - 快速启动脚本

## 使用示例

### 快速开始

```bash
# 设置API密钥
export ANTHROPIC_AUTH_TOKEN="sk-ant-..."

# 启动Alpha
./start.sh
```

### 使用自定义端点

```bash
export ANTHROPIC_AUTH_TOKEN="your-token"
export ANTHROPIC_BASE_URL="https://api.your-company.com"
./start.sh
```

### 切换回OpenAI

编辑config.yaml:
```yaml
llm:
  default_provider: "openai"
```

然后设置:
```bash
export OPENAI_API_KEY="sk-..."
./start.sh
```

## 测试

运行配置测试:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

测试覆盖:
- ✅ 配置文件加载
- ✅ ANTHROPIC_AUTH_TOKEN解析
- ✅ Fallback到ANTHROPIC_API_KEY
- ✅ Base URL设置
- ✅ 模型和参数验证

## 向后兼容

本次更新完全向后兼容:
- ✅ 仍然支持 `ANTHROPIC_API_KEY`
- ✅ OpenAI配置不受影响
- ✅ 现有配置文件仍然有效

如果已经设置了`ANTHROPIC_API_KEY`,无需修改,系统会自动使用。

## 升级步骤

### 从v0.1.0升级

1. 更新配置文件:
```bash
cp config.yaml config.yaml.bak
cp config.example.yaml config.yaml
# 根据需要调整配置
```

2. 设置环境变量:
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

3. 测试配置:
```bash
PYTHONPATH=. python tests/test_config.py
```

4. 启动Alpha:
```bash
./start.sh
```

## 文档更新

- ✅ README.md - 更新安装说明
- ✅ docs/quickstart.md - 更新配置步骤
- ✅ docs/anthropic_config.md - 新增完整配置指南
- ✅ 代码注释更新

## 下一步

建议后续功能:
- [ ] 支持更多环境变量(超时、重试等)
- [ ] 添加配置验证命令
- [ ] 支持配置文件热加载
- [ ] 添加多profile支持

---

**版本**: v0.1.1
**发布日期**: 2026-01-29
**变更类型**: Feature Enhancement
**向后兼容**: Yes
