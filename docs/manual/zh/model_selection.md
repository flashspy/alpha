# 智能多模型选择指南

## 概述

Alpha v0.4.0引入了**智能多模型选择**功能,该功能可以自动分析您的任务并将其路由到最合适的AI模型。这确保了最佳性能,同时最小化API成本。

## 支持的模型

Alpha支持三种DeepSeek模型,每种模型都针对不同的任务类型进行了优化:

### 1. deepseek-chat
**最适合**: 一般对话和简单任务

**特点:**
- 响应速度快
- 日常使用成本效益高
- 擅长问答和简单查询
- 最大tokens: 4096
- Temperature: 0.7

**使用场景:**
- 一般问题("法国的首都是什么?")
- 简单解释
- 基本对话
- 随意的信息查询

### 2. deepseek-coder
**最适合**: 编程和开发任务

**特点:**
- 专门用于代码生成
- 针对开发工作流优化
- 强大的语法理解能力
- 最大tokens: 4096
- Temperature: 0.7

**使用场景:**
- 编写代码("写一个Python函数来排序列表")
- 代码重构
- 修复bug
- 脚本开发
- 代码审查和解释

### 3. deepseek-reasoner
**最适合**: 复杂推理和专家级分析

**特点:**
- 高级推理能力(DeepSeek-R1)
- 处理复杂问题解决
- 适合专家主题
- 最大tokens: 8192
- Temperature: 0.6

**使用场景:**
- 带权衡分析的算法设计
- 系统架构决策
- 分布式系统概念
- 机器学习解释
- 安全分析
- 复杂问题解决

## 工作原理

### 任务难度级别

系统将任务分为四个难度级别:

| 级别 | 描述 | 典型任务 |
|------|------|----------|
| **简单** | 基本问题,简短查询 | "现在几点?", "将10公里转换为英里" |
| **中等** | 中等复杂度,解释 | "解释async/await", "写一个排序函数" |
| **复杂** | 高级编程,重构 | "重构这个类", "优化数据库查询" |
| **专家级** | 分布式系统,机器学习,安全 | "解释Raft共识", "设计容错系统" |

### 自动选择逻辑

模型选择器使用**基于优先级的方法**:

```
优先级1: 专家级/复杂推理任务
  ↓
  deepseek-reasoner

优先级2: 编程任务(无需大量推理)
  ↓
  deepseek-coder

优先级3: 其他任务
  ↓
  基于difficulty_range配置
  (简单/中等任务默认使用deepseek-chat)
```

### 任务分析

系统分析消息中的:

1. **编程关键词**: "write code", "function", "implement", "debug", "refactor"
2. **推理关键词**: "why", "explain", "analyze", "compare", "evaluate"
3. **专家主题**: "machine learning", "distributed system", "cryptography", "scalability"
4. **消息复杂度**: 请求的长度和结构

## 配置

### 启用自动选择

编辑 `config.yaml`:

```yaml
llm:
  default_provider: "deepseek"
  providers:
    deepseek:
      api_key: "${DEEPSEEK_API_KEY}"

      # 启用自动模型选择
      auto_select_model: true

      # 禁用自动选择时的默认模型
      default_model: "deepseek-chat"

      # 模型配置
      models:
        deepseek-chat:
          max_tokens: 4096
          temperature: 0.7
          difficulty_range: ["simple", "medium"]

        deepseek-reasoner:
          max_tokens: 8192
          temperature: 0.6
          difficulty_range: ["complex", "expert"]

        deepseek-coder:
          max_tokens: 4096
          temperature: 0.7
          difficulty_range: ["medium", "complex"]
```

### 禁用自动选择

对所有任务使用特定模型:

```yaml
deepseek:
  auto_select_model: false
  model: "deepseek-coder"  # 始终使用此模型
```

## 使用示例

### 示例1: 简单问题 → deepseek-chat

**用户输入:**
```
法国的首都是什么?
```

**选择的模型:** `deepseek-chat`

**原因:** 简单的事实性查询,不需要编程或复杂推理。

---

### 示例2: 编程任务 → deepseek-coder

**用户输入:**
```
写一个Python函数来递归计算斐波那契数。
```

**选择的模型:** `deepseek-coder`

**原因:** 检测到编程任务(关键词: "写", "函数", "Python"),中等复杂度。

---

### 示例3: 复杂推理 → deepseek-reasoner

**用户输入:**
```
解释不同分布式共识算法(如Raft和Paxos)之间的权衡。
```

**选择的模型:** `deepseek-reasoner`

**原因:** 专家级主题(分布式系统),需要复杂推理和分析。

---

### 示例4: 带推理的代码 → deepseek-reasoner

**用户输入:**
```
设计一个使用JWT令牌的可扩展身份验证系统。解释安全考虑和权衡。
```

**选择的模型:** `deepseek-reasoner`

**原因:** 编程任务 + 推理需求 + 专家主题(安全性、可扩展性)。

## 成本优化

自动模型选择有助于优化成本:

| 场景 | 无自动选择 | 有自动选择 | 节省 |
|------|----------|-----------|------|
| 100个简单查询 | 全部使用reasoner | 100个使用chat | ~40% |
| 50个编程任务 | 全部使用chat | 50个使用coder | 更好的质量 |
| 20个专家分析 | 全部使用chat | 20个使用reasoner | 更好的质量 |

**关键优势:**
1. **降低成本** - 简单任务使用更便宜的模型
2. **更好的质量** - 复杂任务获得专业模型
3. **自动化** - 无需手动选择模型

## 监控

查看日志以了解模型选择决策:

```
INFO: Task analysis - Difficulty: medium, Coding: True, Reasoning: False
INFO: Using deepseek-coder for coding task
INFO: Using DeepSeek model: deepseek-coder (temp=0.7, max_tokens=4096)
```

日志位置: `logs/alpha.log`

## 自定义

### 调整关键词

编辑 `alpha/llm/model_selector.py`:

```python
class TaskAnalyzer:
    CODING_KEYWORDS = [
        'write code', 'function', 'implement',
        # 添加您的自定义关键词
        'create script', 'develop app'
    ]

    EXPERT_KEYWORDS = [
        'machine learning', 'distributed system',
        # 添加您的自定义关键词
        'blockchain', 'kubernetes'
    ]
```

### 修改难度范围

在 `config.yaml` 中,调整哪些模型处理哪些难度级别:

```yaml
models:
  deepseek-chat:
    difficulty_range: ["simple"]  # 仅简单任务

  deepseek-coder:
    difficulty_range: ["medium"]  # 仅中等任务

  deepseek-reasoner:
    difficulty_range: ["complex", "expert"]  # 复杂和专家级
```

## 故障排除

### 选择了错误的模型

**问题:** 期望deepseek-coder但得到了deepseek-chat。

**解决方案:**
1. 检查是否启用了自动选择: `auto_select_model: true`
2. 查看日志中的任务关键词
3. 在请求中添加更具体的关键词
4. 调整配置中的难度范围

**示例修复:**
```
# 不要使用: "写排序代码"
# 使用: "写一个Python函数来实现快速排序"
```

### 模型不可用

**问题:** "Model not found: deepseek-reasoner"

**解决方案:**
1. 验证config.yaml中的`models`部分包含该模型
2. 检查API密钥是否有权访问该模型
3. 确保模型名称拼写正确

### 自动选择不工作

**问题:** 始终使用default_model。

**解决方案:**
1. 检查是否设置了 `auto_select_model: true`
2. 验证models配置存在
3. 检查日志中的选择错误
4. 确保DEEPSEEK_API_KEY有效

## 最佳实践

1. **让自动选择工作** - 除非必要,不要覆盖
2. **使用描述性请求** - 包含有助于分类的关键词
3. **监控日志** - 定期查看选择决策
4. **根据需要调整** - 为您的用例自定义关键词
5. **测试不同措辞** - 查看措辞如何影响选择

## API参考

### TaskDifficulty枚举
```python
class TaskDifficulty(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"
```

### TaskAnalyzer
```python
class TaskAnalyzer:
    @classmethod
    def analyze(cls, messages: List[Dict]) -> TaskCharacteristics
```

### ModelSelector
```python
class ModelSelector:
    def __init__(self, models_config: Dict)

    def select_model(
        self,
        messages: List[Dict],
        default_model: str = "deepseek-chat"
    ) -> str

    def get_model_config(self, model_name: str)
```

## 另见

- [功能指南](features.md) - 完整功能文档
- [DEEPSEEK_MODELS.md](../../DEEPSEEK_MODELS.md) - 技术细节
- [配置指南](../../../README.zh.md#配置) - API设置

---

**版本**: v0.4.0
**更新日期**: 2026-01-29
**状态**: 生产就绪
