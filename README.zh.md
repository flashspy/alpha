# Alpha AI Assistant

[English](README.md) | 简体中文

个人超级AI助理，24小时运行帮助完成各种任务。

## 特性

- 🤖 基于LLM的Agent架构
- 🔧 可扩展的工具系统 (Shell、File、Browser、Code、HTTP、DateTime、Calculator)
- 🧠 长期记忆与个性化
- ⚡ 异步任务管理
- 🔄 持续运行与自动恢复
- 💬 多种交互界面 (CLI、API)
- 🌐 多LLM支持 (Anthropic Claude、OpenAI GPT、DeepSeek)
- 🔌 自定义API端点支持

## 架构

详见 [架构设计文档](docs/zh/architecture.md)。

## 系统要求

- Python 3.10+
- OpenAI API密钥 或 Anthropic API密钥 或 DeepSeek API密钥

## 安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp config.example.yaml config.yaml

# 配置API密钥 (选择一种)

# 方式1: 使用Anthropic Claude
export ANTHROPIC_AUTH_TOKEN="your-api-key"  # 推荐
# 或
export ANTHROPIC_API_KEY="your-api-key"     # 兼容

# 方式2: 使用DeepSeek (经济实惠)
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# 方式3: 使用OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# 可选: 自定义API端点
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

## 使用

```bash
# 启动交互式CLI
python -m alpha.interface.cli

# 或使用快速启动脚本
./start.sh

# 执行特定任务
python -m alpha.main --task "总结AI相关新闻"

# 后台运行
python -m alpha.main --daemon
```

## 示例交互

```
You> 列出当前目录的文件

Alpha> TOOL: shell
PARAMS: {"command": "ls -la"}

执行工具: shell
工具成功: total 48
drwxr-xr-x 10 user staff  320 Jan 29 12:00 .
...

You> 退出
```

## 可用命令

- `help` - 显示帮助信息
- `status` - 显示系统状态
- `clear` - 清空对话历史
- `quit` 或 `exit` - 退出Alpha

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black alpha/
isort alpha/
```

## 项目结构

```
alpha/
├── core/           # 核心运行引擎
├── llm/            # LLM集成
├── tools/          # 工具系统
├── memory/         # 记忆系统
├── tasks/          # 任务管理
├── events/         # 事件系统
├── interface/      # 用户界面
└── utils/          # 工具函数
```

## 文档

### 中文文档
- [快速开始](docs/zh/quickstart.md) - 5分钟上手
- [功能详解](docs/zh/features.md) - 完整功能说明
- [需求文档](docs/zh/requirements.md) - 需求定义
- [架构设计](docs/zh/architecture.md) - 系统架构
- [Anthropic配置](docs/zh/anthropic_config.md) - Anthropic配置指南
- [DeepSeek集成指南](docs/DEEPSEEK_GUIDE.md) - DeepSeek API使用说明
- [API配置](docs/API_SETUP.md) - 多provider配置和故障排查
- [Phase 1报告](docs/zh/phase1_report.md) - 第一阶段开发报告
- [项目总结](docs/zh/project_summary.md) - 项目总结

### English Documentation
- [Quick Start](docs/en/quickstart.md) - Get started in 5 minutes
- [Features](docs/en/features.md) - Complete feature guide
- [Requirements](docs/en/requirements.md) - Requirements definition
- [Architecture](docs/en/architecture.md) - System architecture
- [Anthropic Config](docs/en/anthropic_config.md) - Anthropic configuration guide
- [Phase 1 Report](docs/en/phase1_report.md) - Phase 1 development report
- [Project Summary](docs/en/project_summary.md) - Project summary

### 项目文档
- [变更日志 / Changelog](CHANGELOG.md)
- [版本说明 / Release Notes](RELEASE_NOTES.md)
- [下一步计划 / Next Steps](NEXT_STEPS.md)
- [完成报告 / Completion Report](PROJECT_COMPLETE.md)
- [更新总结 / Update Summary](UPDATE_SUMMARY.md)

## 状态

✅ **Phase 1 Enhanced - Tools Expansion** (已完成)

- [x] 需求定义
- [x] 架构设计
- [x] 核心引擎实现
- [x] LLM集成 (OpenAI, Anthropic, DeepSeek)
- [x] 基础工具 (Shell, File, Search)
- [x] 实用工具 (HTTP, DateTime, Calculator)
- [x] CLI界面
- [x] 测试套件 (32/32 通过)
- [x] 完整文档

## 故障排查

### 导入错误
确保在虚拟环境中:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API密钥错误
检查环境变量是否设置:
```bash
echo $ANTHROPIC_AUTH_TOKEN
```

### 数据库错误
创建数据目录:
```bash
mkdir -p data
```

## LLM Provider 对比

Alpha支持多个LLM provider，您可以根据需求选择：

| Provider | 速度 | 成本 | 中文能力 | 代码能力 | 推理能力 | 推荐场景 |
|----------|------|------|---------|---------|---------|---------|
| **DeepSeek** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 经济实惠、中文任务、日常使用 |
| **Claude** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 复杂推理、代码生成、长文本 |
| **GPT-4** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 通用任务、英文优先 |

### 价格对比（每百万tokens）

| Provider | 输入 | 输出 | 性价比 |
|----------|------|------|--------|
| DeepSeek | $0.14 | $0.28 | 🏆 最佳 |
| Claude Sonnet | $3.00 | $15.00 | 一般 |
| GPT-4 | $5.00 | $15.00 | 较低 |

### 快速测试

```bash
# 测试DeepSeek
export DEEPSEEK_API_KEY="your-key"
python test_deepseek.py

# 测试Anthropic fallback机制
python test_fallback.py

# 检查API配置
./check_api_config.sh
```

### 切换Provider

在 `config.yaml` 中修改：

```yaml
llm:
  default_provider: "deepseek"  # 改为: anthropic, openai, deepseek
```

或在代码中动态选择：

```python
# 使用DeepSeek处理一般对话
response = await llm_service.complete(messages, provider="deepseek")

# 使用Claude处理复杂任务
response = await llm_service.complete(messages, provider="anthropic")
```

## 许可证

MIT

---

**当前版本**: v0.2.0
**状态**: Production Ready - Enhanced Tools
**质量评级**: ⭐⭐⭐⭐⭐
