# DeepSeek API 集成指南

Alpha现在支持DeepSeek官方API服务！

## 什么是DeepSeek？

DeepSeek是一个强大的开源大语言模型，具有以下特点：
- 🚀 高性能推理能力
- 💰 经济实惠的定价
- 🔓 开源模型架构
- 🇨🇳 中文支持优秀

## 获取API密钥

1. 访问 [DeepSeek平台](https://platform.deepseek.com/api_keys)
2. 注册或登录账户
3. 创建新的API密钥
4. 复制密钥（仅显示一次，请妥善保存）

## 配置Alpha使用DeepSeek

### 方法1：设置环境变量

```bash
# 设置DeepSeek API密钥
export DEEPSEEK_API_KEY="your-api-key-here"
```

### 方法2：修改配置文件

编辑 `config.yaml`，将默认provider改为deepseek：

```yaml
llm:
  default_provider: "deepseek"  # 改为使用DeepSeek
  providers:
    deepseek:
      api_key: "${DEEPSEEK_API_KEY}"
      model: "deepseek-chat"
      max_tokens: 4096
      temperature: 0.7
```

## 可用模型

DeepSeek提供以下模型：

### 1. deepseek-chat
- **用途**: 通用对话和问答
- **特点**: 平衡性能和成本
- **推荐场景**: 日常对话、一般性任务

```yaml
model: "deepseek-chat"
```

### 2. deepseek-reasoner (DeepSeek-R1)
- **用途**: 复杂推理和分析
- **特点**: 高级思维链推理能力
- **推荐场景**: 数学问题、逻辑推理、复杂分析

```yaml
model: "deepseek-reasoner"
```

### 3. deepseek-coder
- **用途**: 代码生成和编程
- **特点**: 专注于代码理解和生成
- **推荐场景**: 编程助手、代码审查、bug修复

```yaml
model: "deepseek-coder"
```

## 测试配置

运行测试脚本验证DeepSeek集成：

```bash
# 测试DeepSeek API连接
python test_deepseek.py
```

测试将验证：
- ✅ API密钥是否有效
- ✅ 非流式响应功能
- ✅ 流式响应功能
- ✅ 所有可用模型

## 在Alpha中使用

### 方式1：使用默认provider（推荐）

在 `config.yaml` 中设置 `default_provider: "deepseek"`，然后正常使用：

```bash
./start.sh
```

Alpha会自动使用DeepSeek处理所有对话。

### 方式2：在代码中动态选择

```python
from alpha.llm.service import LLMService, Message

# 创建LLM服务
llm_service = LLMService.from_config(config.llm)

# 使用DeepSeek provider
messages = [Message(role="user", content="你好")]
response = await llm_service.complete(
    messages,
    provider="deepseek"  # 指定使用DeepSeek
)
```

### 方式3：多provider混合使用

```yaml
llm:
  default_provider: "anthropic"  # 默认使用Claude
  providers:
    anthropic:
      # ... Claude配置
    deepseek:
      # ... DeepSeek配置
    openai:
      # ... OpenAI配置
```

然后在需要时切换：

```python
# 使用Claude处理复杂任务
response = await llm_service.complete(messages, provider="anthropic")

# 使用DeepSeek处理一般对话（更经济）
response = await llm_service.complete(messages, provider="deepseek")

# 使用DeepSeek Coder处理代码任务
response = await llm_service.complete(messages, provider="deepseek", model="deepseek-coder")
```

## API特性

DeepSeek API兼容OpenAI格式，支持：

- ✅ **流式响应**: 实时输出生成的文本
- ✅ **非流式响应**: 一次性返回完整响应
- ✅ **温度控制**: 调整输出的随机性
- ✅ **最大token限制**: 控制响应长度
- ✅ **对话历史**: 支持多轮对话上下文

## 定价

DeepSeek提供非常有竞争力的定价：

- **输入**: $0.14 / 百万tokens
- **输出**: $0.28 / 百万tokens

相比其他主流模型，DeepSeek通常便宜5-10倍。

查看最新定价：https://platform.deepseek.com/pricing

## 常见问题

### Q: DeepSeek支持中文吗？
A: 是的！DeepSeek对中文有出色的支持，中文理解和生成能力都很强。

### Q: 可以同时使用多个provider吗？
A: 可以！Alpha支持同时配置多个provider，可以根据任务类型动态选择。

### Q: DeepSeek API有速率限制吗？
A: 有的。具体限制取决于您的账户类型，详见官方文档。

### Q: 如何切换模型？
A: 修改 `config.yaml` 中的 `model` 字段，或在代码中传递 `model` 参数。

## 故障排除

### 错误：未设置API密钥

```bash
export DEEPSEEK_API_KEY="your-api-key"
```

### 错误：401 Unauthorized

检查API密钥是否正确：
1. 访问 https://platform.deepseek.com/api_keys
2. 确认密钥有效
3. 重新设置环境变量

### 错误：429 Rate Limit

您的请求速率过快，请：
1. 减少请求频率
2. 等待一段时间后重试
3. 考虑升级账户

### 错误：网络连接失败

检查网络连接：
```bash
curl https://api.deepseek.com
```

## 性能对比

| Provider | 速度 | 成本 | 中文能力 | 代码能力 | 推理能力 |
|----------|------|------|---------|---------|---------|
| DeepSeek | 快 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Claude | 快 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| GPT-4 | 中 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 相关资源

- [DeepSeek官网](https://www.deepseek.com/)
- [API文档](https://api-docs.deepseek.com/)
- [GitHub](https://github.com/deepseek-ai)
- [定价页面](https://platform.deepseek.com/pricing)

## 示例：完整配置

```yaml
# config.yaml
alpha:
  name: "Alpha Assistant"
  version: "0.1.0"

llm:
  default_provider: "deepseek"
  providers:
    deepseek:
      api_key: "${DEEPSEEK_API_KEY}"
      model: "deepseek-chat"
      max_tokens: 4096
      temperature: 0.7

memory:
  database: "data/alpha.db"
  vector_db: "data/vectors"

tools:
  enabled:
    - shell
    - file
    - search
  sandbox: true

interface:
  cli:
    enabled: true
```

## 下一步

1. 设置API密钥：`export DEEPSEEK_API_KEY="..."`
2. 运行测试：`python test_deepseek.py`
3. 启动Alpha：`./start.sh`
4. 开始使用！

享受DeepSeek强大的AI能力吧！🚀
