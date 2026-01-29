# 工具调用解析器增强

## 问题描述

用户在使用Alpha时，看到了工具调用的内部细节（TOOL和PARAMS行）：

```
You: 成都今天天气如何

Alpha: 我来帮您查询成都今天的天气情况。

TOOL: http
PARAMS:
  url: "https://wttr.in/成都?format=j1&lang=zh-cn"
  method: "GET"
```

这违反了设计原则：**用户不应该看到Agent与LLM之间的技术交互细节**。

## 根本原因

1. **LLM使用了多行YAML格式**而不是单行JSON格式来输出PARAMS
2. **原始解析器只支持单行JSON**，无法识别多行YAML格式
3. 未被识别的TOOL/PARAMS行没有被过滤，直接显示给了用户

## 解决方案

### 1. 增强 `_parse_tool_calls` 方法

支持三种格式的PARAMS：

#### 格式1：单行JSON（原有格式）
```
TOOL: http
PARAMS: {"url": "https://example.com", "method": "GET"}
```

#### 格式2：多行YAML（新增支持）
```
TOOL: http
PARAMS:
  url: "https://example.com"
  method: "GET"
```

#### 格式3：复杂嵌套YAML
```
TOOL: http
PARAMS:
  url: "https://api.example.com"
  headers:
    Content-Type: "application/json"
  json:
    query: "test"
```

### 2. 增强 `_extract_user_message` 方法

支持过滤多行PARAMS块：

```python
def _extract_user_message(self, response: str) -> str:
    """Extract user-facing message by removing tool call lines."""
    lines = response.split('\n')
    user_lines = []
    in_params_block = False

    for line in lines:
        if line.startswith("TOOL:"):
            continue  # 跳过TOOL行
        elif line.startswith("PARAMS:"):
            in_params_block = True  # 开始PARAMS块
            continue
        elif in_params_block:
            # 检查是否是缩进行（PARAMS块的一部分）
            if line and (line.startswith('  ') or line.startswith('\t')):
                continue  # 跳过缩进行
            else:
                in_params_block = False  # PARAMS块结束

        user_lines.append(line)

    return '\n'.join(user_lines).strip()
```

### 3. 更新系统提示词

明确告知LLM：

1. 支持两种PARAMS格式（JSON和YAML）
2. **工具调用行对用户不可见**
3. 用户只看到自然语言消息

```
CRITICAL: Tool call lines (TOOL: and PARAMS:) are automatically hidden from users.
Users NEVER see these technical details - they only see your natural language messages.
```

## 测试验证

创建了 `tests/test_parser.py` 测试所有格式：

```bash
$ python tests/test_parser.py

Test 1: Single-line JSON format
✓ Tool calls parsed: 1
✓ User message correctly filtered

Test 2: Multi-line YAML format
✓ Tool calls parsed: 1
✓ User message correctly filtered

Test 3: Multiple tools (mixed format)
✓ Tool calls parsed: 2
✓ User message correctly filtered

Test 4: Complex YAML structure
✓ Tool calls parsed: 1
✓ User message correctly filtered
```

所有25个综合测试继续通过：
```
✓ All tests passed! (100.0%)
```

## 用户体验改进

### 修复前（错误）：
```
You: 成都今天天气如何

Alpha: 我来帮您查询成都今天的天气情况。

TOOL: http          ← ❌ 用户不应看到
PARAMS:             ← ❌ 用户不应看到
  url: "..."        ← ❌ 用户不应看到
  method: "GET"     ← ❌ 用户不应看到
```

### 修复后（正确）：
```
You: 成都今天天气如何

Alpha: 我来帮您查询成都今天的天气情况。

[工具在后台静默执行]

Alpha: 成都今天天气晴朗，温度15°C，湿度45%...
```

## 技术要点

1. **PyYAML依赖**：已在 `requirements.txt` 中（pyyaml>=6.0）
2. **解析优先级**：先尝试JSON，再尝试YAML
3. **健壮性**：解析失败时记录警告但不崩溃
4. **向后兼容**：完全兼容原有的单行JSON格式

## 相关文件

- `alpha/interface/cli.py:211` - `_parse_tool_calls()` 方法
- `alpha/interface/cli.py:290` - `_extract_user_message()` 方法
- `tests/test_parser.py` - 解析器单元测试
- `tests/test_cli_comprehensive.py` - 综合集成测试

## 结论

通过增强解析器和消息过滤器，Alpha现在能够：

✅ 支持LLM使用任意格式（JSON或YAML）输出工具调用
✅ 完全隐藏工具调用的技术细节
✅ 向用户提供纯净的自然语言交互体验
✅ 保持向后兼容性

用户体验得到显著提升，符合"隐藏技术复杂度"的设计原则。
