# Agent技能使用指南

## 简介

Alpha的Agent技能系统允许您通过自动发现和安装技能来**动态扩展其功能**。与内置工具不同,技能是模块化的、有版本控制的,并且可以由社区贡献。

## 快速开始

### 在对话中使用技能

技能会在需要时自动发现和安装:

```
You: 将"hello world"转换为大写

Alpha: 我将使用text-processing技能。

SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

Result: "HELLO WORLD"
```

无需手动安装 - Alpha会自动处理!

### CLI命令

```bash
# 列出已安装的技能
skills

# 搜索技能
search skill text
search skill json
search skill data

# 获取帮助
help skills
```

## 内置技能

Alpha附带**3个预装的内置技能**,可立即使用:

### 1. text-processing
20+文本操作,用于常见的文本处理任务。

**可用操作:**

**大小写转换:**
```python
# 大写
operation: "uppercase"
text: "hello world"
Result: "HELLO WORLD"

# 小写
operation: "lowercase"
text: "HELLO WORLD"
Result: "hello world"

# 标题大小写
operation: "titlecase"
text: "hello world"
Result: "Hello World"

# 首字母大写
operation: "capitalize"
text: "hello world"
Result: "Hello world"
```

**字符串操作:**
```python
# 反转
operation: "reverse"
text: "hello"
Result: "olleh"

# 去除空白
operation: "trim"
text: "  hello  "
Result: "hello"
```

**提取:**
```python
# 提取邮箱
operation: "extract_emails"
text: "联系: john@example.com 或 jane@test.org"
Result: ["john@example.com", "jane@test.org"]

# 提取URL
operation: "extract_urls"
text: "访问 https://example.com 或 http://test.org"
Result: ["https://example.com", "http://test.org"]

# 提取数字
operation: "extract_numbers"
text: "有42个苹果和15个橙子"
Result: [42.0, 15.0]
```

**完整操作列表:**
- uppercase, lowercase, titlecase, capitalize
- reverse, trim, strip
- split, join, replace, remove
- count_words, count_chars, count_lines
- extract_emails, extract_urls, extract_numbers
- truncate, pad_left, pad_right

### 2. json-processor
8种JSON操作,用于解析、格式化和转换。

**可用操作:**

```python
# 解析JSON字符串
operation: "parse"
json_str: '{"name": "Alpha", "version": "1.0"}'
Result: {"name": "Alpha", "version": "1.0"}

# 格式化JSON(美化输出)
operation: "format"
json_str: '{"name":"Alpha"}'
indent: 2
Result: {
  "name": "Alpha"
}

# 压缩JSON
operation: "minify"
json_str: '{  "name":  "Alpha"  }'
Result: '{"name":"Alpha"}'

# 验证JSON
operation: "validate"
json_str: '{"valid": true}'
Result: {"valid": true, "error": null}

# 按路径提取值
operation: "extract"
json_str: '{"user": {"name": "Alice", "age": 30}}'
path: "user.name"
Result: "Alice"

# 合并多个JSON对象
operation: "merge"
json_objects: [{"a": 1}, {"b": 2}, {"c": 3}]
Result: {"a": 1, "b": 2, "c": 3}

# 按键过滤
operation: "filter"
json_str: '{"a": 1, "b": 2, "c": 3}'
keys: ["a", "c"]
Result: {"a": 1, "c": 3}
```

**完整操作列表:**
- parse, stringify, format, minify
- validate, extract, merge, filter

### 3. data-analyzer
17种统计操作,用于数据分析和聚合。

**可用操作:**

**基础统计:**
```python
# 平均值
operation: "mean"
data: [1, 2, 3, 4, 5]
Result: 3.0

# 中位数
operation: "median"
data: [1, 2, 3, 4, 5]
Result: 3.0

# 众数(最常见)
operation: "mode"
data: [1, 2, 2, 3, 3, 3]
Result: 3

# 最小值、最大值、范围
operation: "min"
data: [10, 5, 20, 15]
Result: 5

operation: "max"
data: [10, 5, 20, 15]
Result: 20

operation: "range"
data: [10, 5, 20, 15]
Result: 15  # max - min
```

**高级统计:**
```python
# 标准差
operation: "stdev"
data: [2, 4, 6, 8, 10]
Result: 2.8284

# 方差
operation: "variance"
data: [2, 4, 6, 8, 10]
Result: 8.0

# 百分位数
operation: "percentile"
data: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
percentile: 75
Result: 7.75
```

**数据操作:**
```python
# 按键分组
operation: "group_by"
data: [
  {"type": "A", "value": 1},
  {"type": "B", "value": 2},
  {"type": "A", "value": 3}
]
key: "type"
Result: {
  "A": [{"type": "A", "value": 1}, {"type": "A", "value": 3}],
  "B": [{"type": "B", "value": 2}]
}

# 聚合
operation: "aggregate"
data: [
  {"category": "fruit", "price": 10},
  {"category": "fruit", "price": 15},
  {"category": "veg", "price": 5}
]
group_key: "category"
value_key: "price"
agg_func: "sum"
Result: {"fruit": 25, "veg": 5}

# 排序数据
operation: "sort"
data: [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]
key: "age"
Result: [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]

# 获取统计摘要
operation: "summary"
data: [10, 20, 30, 40, 50]
Result: {
  "count": 5,
  "mean": 30.0,
  "median": 30.0,
  "min": 10,
  "max": 50,
  "stdev": 14.14,
  "variance": 200.0
}
```

**完整操作列表:**
- mean, median, mode, min, max, range, sum, count
- variance, stdev, percentile, quartiles
- group_by, aggregate, sort, filter, summary

## 自定义技能

### 安装自定义技能

来自市场的技能在被引用时会自动安装:

```
You: 使用weather-api技能获取北京的天气

Alpha: 正在安装weather-api技能...
正在安装依赖...
技能安装成功!

[执行weather-api技能]
```

### 创建您自己的技能

创建新的技能目录:

```
my-custom-skill/
├── skill.yaml        # 元数据(必需)
├── skill.py          # 实现(必需)
├── README.md         # 文档(可选)
└── requirements.txt  # 依赖(可选)
```

**skill.yaml:**
```yaml
name: my-custom-skill
version: "1.0.0"
description: "我的自定义技能"
author: "您的名字"
category: "utility"
tags:
  - helper
  - automation
dependencies:
  - requests
python_version: ">=3.8"
homepage: "https://github.com/user/my-custom-skill"
repository: "https://github.com/user/my-custom-skill"
license: "MIT"
```

**skill.py:**
```python
from alpha.skills.base import AgentSkill, SkillResult

class MyCustomSkill(AgentSkill):
    """我的自定义技能实现。"""

    async def initialize(self) -> bool:
        """初始化技能。"""
        # 设置资源、加载模型等
        return True

    async def execute(self, **kwargs) -> SkillResult:
        """
        执行技能。

        Args:
            **kwargs: 技能特定参数

        Returns:
            SkillResult
        """
        try:
            # 您的技能逻辑
            param1 = kwargs.get('param1')
            result = f"已处理: {param1}"

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
        """清理资源。"""
        pass

    def get_schema(self):
        """定义参数模式。"""
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "第一个参数"
                }
            },
            "required": ["param1"]
        }
```

### 发布技能

1. 为您的技能创建GitHub仓库
2. 将其添加到技能市场注册表
3. 向Alpha技能仓库提交pull request

## 最佳实践

### 何时使用技能 vs 工具

| 特性 | 工具 | 技能 |
|------|------|------|
| 内置 | 是 | 否 |
| 安装 | 始终可用 | 按需自动安装 |
| 版本控制 | 否 | 是 |
| 依赖 | 否 | 是 |
| 社区贡献 | 否 | 是 |

**使用工具用于:**
- 核心系统操作(shell、file、HTTP)
- 始终需要的功能
- 简单、独立的操作

**使用技能用于:**
- 专业功能
- 特定领域的操作
- 需要外部依赖的操作
- 社区贡献的能力

### 技能开发技巧

1. **单一职责** - 每个技能应该做好一件事
2. **清晰的参数** - 使用描述性名称并提供模式
3. **错误处理** - 始终返回有意义的错误消息
4. **文档** - 包含全面的README
5. **测试** - 为您的技能编写测试
6. **性能** - 在`initialize()`中延迟加载重资源

## 故障排除

### 找不到技能

**问题:**
```
Error: Skill not found: my-skill
```

**解决方案:**
1. 启用自动安装(默认已启用)
2. 检查技能名称拼写
3. 验证技能存在于市场中
4. 检查网络连接

### 安装失败

**问题:**
```
Error: Failed to install skill: my-skill
```

**解决方案:**
1. 检查互联网连接
2. 验证Python版本兼容性
3. 手动安装依赖: `pip install -r requirements.txt`
4. 检查仓库URL是否可访问

### 执行失败

**问题:**
```
Error: Missing required parameters: ['param1']
```

**解决方案:**
1. 提供所有必需参数
2. 检查技能文档中的参数名称
3. 验证参数类型与模式匹配

### 内置技能未加载

**问题:**
```
Builtin skills not found
```

**解决方案:**
1. 检查`alpha/skills/builtin/`目录是否存在
2. 验证所有skill.yaml文件存在
3. 重启Alpha
4. 检查`logs/alpha.log`中的日志

## 高级用法

### 编程使用

```python
from alpha.skills.executor import SkillExecutor
from alpha.skills.registry import SkillRegistry
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.installer import SkillInstaller

# 设置
registry = SkillRegistry()
marketplace = SkillMarketplace()
installer = SkillInstaller()
executor = SkillExecutor(
    registry=registry,
    marketplace=marketplace,
    installer=installer,
    auto_install=True
)

# 执行技能
result = await executor.execute(
    "text-processing",
    operation="uppercase",
    text="hello world"
)

if result.success:
    print(result.output)  # "HELLO WORLD"
else:
    print(f"Error: {result.error}")
```

### 禁用自动安装

如果您更喜欢手动控制:

```python
executor = SkillExecutor(
    registry=registry,
    marketplace=marketplace,
    installer=installer,
    auto_install=False  # 禁用自动安装
)

# 现在您必须手动安装技能
await installer.install(skill_path)
```

## 另见

- [Agent技能文档](../../AGENT_SKILLS.md) - 技术文档
- [内置技能参考](../../BUILTIN_SKILLS.md) - 完整的内置技能参考
- [功能指南](features.md) - 所有Alpha功能

---

**版本**: v0.4.0
**更新日期**: 2026-01-29
**状态**: 生产就绪
