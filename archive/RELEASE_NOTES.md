[English](#english) | [简体中文](#中文)

---

# <a name="english"></a>English

# Alpha v0.1.0 - Release Notes

## Release Information

- **Version**: 0.1.0
- **Codename**: Foundation
- **Release Date**: 2026-01-29
- **Development Stage**: Phase 1 Complete
- **Status**: Production Ready (Personal Use)

## New Features

### Core System
- ✅ 24/7 continuous running engine
- ✅ Event-driven architecture
- ✅ Asynchronous task management system
- ✅ SQLite persistent storage
- ✅ Health monitoring and status reporting

### LLM Integration
- ✅ OpenAI GPT-4/GPT-3.5 integration
- ✅ Anthropic Claude integration
- ✅ Streaming response support
- ✅ Automatic multi-provider switching

### Tool System
- ✅ Shell command execution tool
- ✅ File operation tools (read/write/delete/list)
- ✅ Web search tool (placeholder)
- ✅ Extensible plugin architecture

### Memory & Storage
- ✅ Conversation history recording
- ✅ Task execution logs
- ✅ System event logging
- ✅ Knowledge base storage

### User Interface
- ✅ Interactive CLI interface
- ✅ Rich terminal UI
- ✅ Streaming response display
- ✅ Command support (help/status/clear/quit)

## Technical Specifications

### System Requirements
- Python 3.10+
- Linux/macOS/Windows (WSL)
- At least 100MB disk space
- Network connection (for LLM API access)

### Performance Metrics
- Startup time: < 2 seconds
- Memory usage: ~50-100MB
- Database queries: < 100ms
- LLM response: 1-5 seconds (depending on provider)

### Code Statistics
- Python files: 15 modules
- Lines of code: ~2253 lines
- Test cases: 4
- Test pass rate: 100%
- Documentation pages: 6

## Installation & Usage

### Quick Installation
```bash
# Clone or enter project directory
cd agents-7b5dad6160

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config.example.yaml config.yaml
# Edit config.yaml to add API keys

# Start Alpha
python -m alpha.interface.cli
```

### Configuration Example
```yaml
llm:
  default_provider: "openai"
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4"
```

## Known Issues

1. **SearchTool placeholder implementation** - Needs real search API integration
2. **No sandbox isolation** - Shell and File tools lack security isolation
3. **Single-user mode** - Multi-user support not available
4. **Simple error recovery** - Recovery strategies need enhancement

## Limitations & Precautions

### Security Limitations
⚠️ Shell tools execute with current user privileges
⚠️ File operations can access entire file system
⚠️ No user authentication mechanism

**Recommendation**: Use only in trusted environments

### Feature Limitations
- Only supports OpenAI and Anthropic providers
- No vector search capability
- No browser automation
- No scheduled task scheduling

## Upgrade Path

Upgrading from blank project to v0.1.0:
```bash
# This is a brand new implementation, no upgrade needed
# Just follow the installation instructions
```

## Documentation Resources

- [Quick Start](docs/quickstart.md) - Get started in 5 minutes
- [Feature Details](docs/features.md) - Complete feature description
- [Architecture Design](docs/architecture.md) - Technical architecture
- [Project Summary](docs/project_summary.md) - Development summary

## Next Version Preview (v0.2.0)

Planned features:
- 🔄 Browser automation (Playwright)
- 🔄 Vector database integration (ChromaDB)
- 🔄 Semantic search functionality
- 🔄 RESTful API interface
- 🔄 Scheduled task scheduling
- 🔄 Code execution sandbox

Expected release: After Phase 2 completion

## Contributors

- Alpha Development Team

## License

MIT License

---

**Thank you for using Alpha AI Assistant!**

For questions, please refer to the documentation or submit an issue.

---

# <a name="中文"></a>简体中文

# Alpha v0.1.0 - Release Notes

## 发布信息

- **版本**: 0.1.0
- **代号**: Foundation (基础版)
- **发布日期**: 2026-01-29
- **开发阶段**: Phase 1 Complete
- **状态**: Production Ready (个人使用)

## 新增功能

### 核心系统
- ✅ 24/7持续运行引擎
- ✅ 事件驱动架构
- ✅ 异步任务管理系统
- ✅ SQLite持久化存储
- ✅ 健康监控和状态报告

### LLM集成
- ✅ OpenAI GPT-4/GPT-3.5集成
- ✅ Anthropic Claude集成
- ✅ 流式响应支持
- ✅ 多provider自动切换

### 工具系统
- ✅ Shell命令执行工具
- ✅ 文件操作工具(读/写/删/列表)
- ✅ Web搜索工具(占位)
- ✅ 可扩展插件架构

### 记忆与存储
- ✅ 对话历史记录
- ✅ 任务执行日志
- ✅ 系统事件记录
- ✅ 知识库存储

### 用户界面
- ✅ 交互式CLI界面
- ✅ Rich终端UI
- ✅ 流式响应显示
- ✅ 命令支持(help/status/clear/quit)

## 技术规格

### 系统要求
- Python 3.10+
- Linux/macOS/Windows (WSL)
- 至少100MB磁盘空间
- 网络连接(访问LLM API)

### 性能指标
- 启动时间: < 2秒
- 内存占用: ~50-100MB
- 数据库查询: < 100ms
- LLM响应: 1-5秒(取决于provider)

### 代码统计
- Python文件: 15个模块
- 代码行数: ~2253行
- 测试用例: 4个
- 测试通过率: 100%
- 文档页面: 6个

## 安装与使用

### 快速安装
```bash
# 克隆或进入项目目录
cd agents-7b5dad6160

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp config.example.yaml config.yaml
# 编辑config.yaml添加API密钥

# 启动Alpha
python -m alpha.interface.cli
```

### 配置示例
```yaml
llm:
  default_provider: "openai"
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4"
```

## 已知问题

1. **SearchTool占位实现** - 需要集成真实搜索API
2. **无沙箱隔离** - Shell和File工具无安全隔离
3. **单用户模式** - 暂不支持多用户
4. **错误恢复简单** - 恢复策略需要增强

## 限制与注意事项

### 安全限制
⚠️ Shell工具在当前用户权限下执行
⚠️ 文件操作可访问整个文件系统
⚠️ 无用户认证机制

**建议**: 仅在受信任环境中使用

### 功能限制
- 仅支持OpenAI和Anthropic两家provider
- 无向量搜索能力
- 无浏览器自动化
- 无定时任务调度

## 升级路径

从空白项目升级到v0.1.0:
```bash
# 项目已是全新实现,无需升级
# 直接按照安装说明使用
```

## 文档资源

- [快速开始](docs/quickstart.md) - 5分钟上手
- [功能详解](docs/features.md) - 完整功能说明
- [架构设计](docs/architecture.md) - 技术架构
- [项目总结](docs/project_summary.md) - 开发总结

## 下一版本预告 (v0.2.0)

计划功能:
- 🔄 浏览器自动化(Playwright)
- 🔄 向量数据库集成(ChromaDB)
- 🔄 语义搜索功能
- 🔄 RESTful API接口
- 🔄 定时任务调度
- 🔄 代码执行沙箱

预计发布: Phase 2完成后

## 贡献者

- Alpha Development Team

## 许可证

MIT License

---

**感谢使用Alpha AI Assistant!**

如有问题,请查阅文档或提交issue。
