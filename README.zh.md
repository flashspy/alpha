# Alpha：由AI自己定义并实现的 AI 助手
通过 `cat make_alpha.md | claude --dangerously-skip-permissions` 命令构建

[English](README.md) | 简体中文

一个全天候运行的个人超级AI助手,帮助您完成各种任务。

## Alpha是什么?

Alpha是由先进AI模型驱动的智能个人助手。它可以:

- 💬 **自然对话** - 与您聊天并帮助处理日常任务
- 🔧 **执行任务** - 运行shell命令、管理文件、发送HTTP请求
- 📅 **定时任务** - 使用类似cron的方式设置自动化任务
- 🧮 **计算转换** - 解决数学问题和单位转换
- 🌐 **搜索网络** - 在线查找信息
- ⏰ **处理时间** - 处理日期、时间和时区
- 🤖 **多AI支持** - 可选择DeepSeek、Claude或GPT-4
- 🧠 **智能模型选择** - 自动任务分析和最优模型路由
- 🎯 **动态技能** - 通过可自动安装的技能扩展能力
- ⚡ **内置技能** - 3个预装技能即开即用(文本、JSON、数据处理)
- 🛡️ **永不放弃的韧性** - 自动故障恢复、熔断器和自愈能力

## 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/flashspy/alpha.git
cd alpha

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows系统: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 创建数据目录
mkdir -p data
```

### 2. 配置API密钥

选择一个AI提供商(推荐使用DeepSeek,性价比最高):

```bash
# 选项1: DeepSeek (推荐 - 性价比最高)
export DEEPSEEK_API_KEY="你的deepseek密钥"

# 选项2: Anthropic Claude
export ANTHROPIC_API_KEY="你的anthropic密钥"

# 选项3: OpenAI GPT
export OPENAI_API_KEY="你的openai密钥"
```

**获取API密钥:**
- DeepSeek: https://platform.deepseek.com/api_keys
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys

### 3. 启动Alpha

```bash
# 快速启动
./start.sh

# 或手动启动
python -m alpha.interface.cli
```

## 使用示例

### 基本对话

```
You> 北京今天天气怎么样?
Alpha> 我来帮您查询北京今天的天气。
[显示天气信息]

You> 计算2500的15%是多少
Alpha> 结果是: 375.0

You> 这个目录里有什么文件?
Alpha> [列出当前目录的所有文件]
```

### 可用命令

与Alpha对话时,可以使用这些命令:

- `help` - 显示可用命令
- `status` - 查看Alpha的系统状态
- `clear` - 清除对话历史
- `exit` 或 `quit` - 退出Alpha

## AI提供商对比

Alpha支持三种AI提供商。根据您的需求选择:

| 特性 | DeepSeek | Claude | GPT-4 |
|------|----------|--------|-------|
| **成本** | 🏆 最优 | 良好 | 昂贵 |
| **速度** | 非常快 | 快 | 中等 |
| **中文支持** | 优秀 | 良好 | 一般 |
| **代码生成** | 非常好 | 优秀 | 非常好 |
| **推理能力** | 优秀 | 优秀 | 非常好 |
| **最适合** | 日常使用,成本敏感 | 复杂任务,编程 | 通用任务 |

### 价格对比

每百万tokens成本:

| 提供商 | 输入 | 输出 | **总计** |
|--------|------|------|----------|
| **DeepSeek** | $0.14 | $0.28 | **$0.42** 🏆 |
| Claude Sonnet | $3.00 | $15.00 | $18.00 |
| GPT-4 | $5.00 | $15.00 | $20.00 |

💡 **DeepSeek可为您节省40-50倍的API成本!**

### 切换提供商

编辑 `config.yaml`:

```yaml
llm:
  default_provider: "deepseek"  # 改为: anthropic, openai, 或 deepseek
```

## 守护进程模式 - 全天候运行

在Linux上将Alpha作为后台服务运行:

```bash
# 安装为systemd服务
sudo ./scripts/install_daemon.sh

# 启动服务
sudo systemctl start alpha

# 开机自动启动
sudo systemctl enable alpha

# 查看状态
sudo systemctl status alpha

# 查看日志
sudo journalctl -u alpha -f
```

**功能特性:**
- 24/7后台运行
- 失败自动重启
- 开机自动启动
- 优雅关闭
- 无需重启即可重载配置

详细设置说明请参阅[守护进程模式指南](docs/manual/zh/daemon_mode.md)。

## 可用工具

Alpha内置强大的工具:

| 工具 | 功能 | 使用示例 |
|------|------|----------|
| **Shell** | 执行终端命令 | `ls`, `git status`, `npm install` |
| **File** | 读写管理文件 | 创建、编辑、删除文件 |
| **HTTP** | 发送网络请求 | 调用API、下载内容 |
| **Search** | 搜索网络 | 在线查找信息 |
| **DateTime** | 处理日期时间 | 转换时区、计算时长 |
| **Calculator** | 数学和单位转换 | `sqrt(144)`, 10公里转英里 |

## 定时任务

让Alpha自动执行任务:

```
You> 安排一个任务,每天早上9点检查我的邮件
Alpha> 我会为您设置定时任务...
[创建cron计划: 0 9 * * *]
```

调度格式:
- **Cron表达式**: `0 9 * * *` (每天早上9点)
- **间隔**: 每30分钟、每2小时
- **一次性**: 指定的日期和时间

## 版本发布记录

### v0.10.0 (最新版本) - 高级智能与自我进化
**发布日期**: 2026-01-31

**新功能:**
- 🧠 **主动智能系统** - 在用户提问前预判需求
  - PatternLearner - 从用户行为和对话历史中学习
  - TaskDetector - 自动检测主动任务机会
  - Predictor - 预测用户需求和最佳时机
  - Notifier - 智能通知系统
- 📊 **多模型性能追踪** - 动态优化AI模型选择
  - ModelPerformanceTracker - 跟踪每个模型的成本、延迟、质量
  - ModelOptimizer - 基于学习的性能动态选择模型
  - 成本-性能权衡分析和推荐
- 🎯 **Agent基准测试框架** - 行业标准性能测量
  - 受GAIA启发的复杂度分层(4个级别)
  - 多维度评估(7个指标)
  - 自动化基准测试运行器和综合报告
  - 性能回归检测
- 🔄 **自我进化技能库** - 自主技能管理
  - 主动探索和发现新技能
  - 智能评估和质量评估
  - 基于性能的优化和修剪
  - 指标持久化和历史追踪

**架构:**
- 4个新子系统: 主动智能、模型性能、基准测试、技能进化
- 162个综合测试(100%通过率)
- 约6,000行生产就绪代码
- 与现有Alpha基础设施完全集成

**生产收益:**
- **主动性**: Alpha现在能预判需求而非仅被动响应
- **成本优化**: 动态模型选择可减少高达40%的API成本
- **自我改进**: 无需人工干预的持续学习和优化
- **可测量**: 采用行业标准的客观性能基准

**文档:**
- [主动智能指南](docs/manual/zh/proactive_intelligence.md) (待完善)
- [模型性能追踪](docs/manual/zh/model_performance.md) (待完善)
- [基准测试](docs/manual/zh/benchmarks.md) (待完善)

### v0.9.0 - 自我改进循环基础设施
**发布日期**: 2026-01-31

**新功能:**
- 🔄 **自我改进循环** - 从执行模式中持续学习
  - LogAnalyzer - 从执行日志中检测模式和低效问题
  - ImprovementExecutor - 自动应用优化
  - LearningStore - 持久化学习数据库
  - FeedbackLoop - 编排持续改进周期

### v0.8.0 - 浏览器自动化系统
**发布日期**: 2026-01-31

**新功能:**
- 🌐 **Playwright浏览器自动化**
  - 多浏览器支持(Chromium、Firefox、WebKit)
  - 智能网页抓取和数据提取
  - 表单自动化和元素交互
  - 屏幕截图和视觉测试
  - 8层安全模型

### v0.7.0 - 代码生成与安全执行
**发布日期**: 2026-01-30

**新功能:**
- 🔧 **代码生成引擎** - LLM驱动的Python、JavaScript、Bash代码生成
  - 从任务描述进行上下文感知的代码生成
  - 自动测试生成(pytest/jest/bats模板)
  - 基于执行反馈的迭代代码优化
  - 多格式响应解析(JSON、markdown、raw)
  - 特定语言的模板和最佳实践
- 🛡️ **安全执行沙箱** - 基于Docker的隔离执行环境
  - 容器隔离,只读根文件系统
  - 资源限制: CPU 50%、内存256MB、默认超时30秒
  - 网络隔离(默认禁用,可配置)
  - 自动容器清理和资源管理
  - Docker不可用时优雅降级
- ✅ **代码验证系统** - 多阶段验证管道
  - 使用AST解析的语法验证(Python)和模式匹配(JavaScript、Bash)
  - 危险操作的安全扫描(eval、exec、文件删除、网络访问)
  - 风险级别评估(低、中、高)
  - 代码质量评分和指标(复杂度、文档、错误处理)
  - 特定语言的安全建议
- ⚡ **代码执行工具** - 与Alpha工具系统集成
  - 作为标准工具无缝集成LLM agent
  - 基于任务的生成或直接代码执行
  - 带代码预览的用户批准工作流
  - 智能重试逻辑和自动优化
  - 全面的统计和执行跟踪
- 🎯 **多语言支持** - 全面支持3种语言
  - Python 3.12+ (基于ast的验证)
  - JavaScript/Node.js 20+ (基于模式的验证)
  - Bash 5.2+ (构造验证)
  - 特定语言的执行配置
  - 依赖检测和管理

**架构:**
- 5个核心组件: CodeGenerator、CodeValidator、SandboxManager、CodeExecutor、CodeExecutionTool
- 3,859行生产就绪代码
- 86个综合测试(100%通过率)
- 18,300行文档(中英文)
- 事件驱动架构实现松耦合
- 配置驱动行为

**安全性:**
- 8层安全模型(输入验证、代码扫描、沙箱、资源限制、网络隔离、用户批准、审计日志、紧急停止)
- 恶意代码检测(eval、exec、subprocess、文件删除、网络访问)
- 使用seccomp配置文件的容器隔离
- 只读根文件系统,可写/tmp
- 严格强制资源限制
- 默认需要用户批准
- 全面的审计日志

**生产收益:**
- **自主能力**: 现有工具不足时生成并执行自定义代码
- **默认安全**: 多层安全防止恶意代码执行
- **用户控制**: 批准工作流确保透明度
- **智能化**: 失败时自动优化,带改进的重试
- **可观察**: 详细的执行日志和统计
- **灵活性**: 支持Python、JavaScript、Bash,架构可扩展

**文档:**
- [代码执行指南(中文)](docs/manual/zh/code_execution.md)
- [代码执行指南(英文)](docs/manual/en/code_execution.md)
- [架构文档](docs/internal/code_execution_architecture.md)
- [API参考](docs/internal/code_execution_api.md)
- [测试报告](docs/internal/code_execution_test_report.md)

### v0.6.0 - 永不放弃的韧性系统
**发布日期**: 2026-01-30

**新功能:**
- 🛡️ **永不放弃的韧性系统** - 全面的故障恢复和自愈
  - **核心韧性管理器** - 集中式故障检测和恢复编排
  - **熔断器系统** - 通过自动状态管理防止级联故障
    - 三种状态: CLOSED(正常)、OPEN(阻塞)、HALF_OPEN(测试)
    - 可配置的故障阈值和恢复超时
    - 基于健康指标的自动状态转换
  - **重试策略引擎** - 具有多种策略的智能重试机制
    - 带抖动的指数退避,避免惊群效应
    - 线性、固定间隔和立即重试策略
    - 每个操作可配置的重试限制和退避倍数
  - **优雅降级管理器** - 故障期间保持部分功能
    - 关键操作的回退策略
    - 服务不可用时提供缓存响应
    - 数据库连接故障时的只读模式
  - **健康检查系统** - 主动监控和自愈
    - 对所有关键组件进行定期健康检查
    - 基于健康状态的自动恢复操作
    - 系统级健康聚合和报告
  - **恢复策略协调器** - 智能恢复决策
    - 基于优先级的恢复策略选择
    - 上下文感知的恢复操作
    - 复杂场景的组合策略支持

**架构:**
- 6个核心组件协同工作
- 3,459行生产就绪代码
- 15个综合测试用例(14个通过 = 93%成功率)
- 事件驱动架构实现松耦合
- 配置驱动行为,易于定制

**生产收益:**
- **提高正常运行时间**: 从临时故障自动恢复
- **防止级联**: 熔断器阻止故障传播
- **更好的用户体验**: 优雅降级保持部分功能
- **主动性**: 健康检查在影响用户前检测问题
- **可观察**: 全面的指标和健康状态

**文档:**
- [韧性系统文档](docs/RESILIENCE_SYSTEM.md)
- [健康检查配置](docs/HEALTH_CHECK_GUIDE.md)

### v0.5.0 - 守护进程模式与24/7运行
**发布日期**: 2026-01-30

**新功能:**
- 🌙 **守护进程模式** - 将Alpha作为24/7后台服务运行
  - 为Linux系统集成systemd
  - 系统启动时自动启动
  - 失败时自动重启(可配置重试策略)
  - 优雅关闭处理(SIGTERM)
  - 无需重启即可重载配置(SIGHUP)
- 🔧 **服务管理** - 完整的systemd服务生命周期
  - 安装/卸载脚本
  - PID文件管理
  - 信号处理(SIGTERM、SIGHUP、SIGINT)
  - 后台进程分离
- 📊 **生产就绪** - 适合服务器部署
  - 非root用户执行
  - 资源限制配置
  - 安全加固选项
  - 向systemd日志的全面记录

**文档:**
- [守护进程模式指南](docs/manual/zh/daemon_mode.md)
- [Systemd配置](systemd/README.md)

### v0.4.0 - 智能多模型选择
**发布日期**: 2026-01-29

**新功能:**
- ✨ **智能模型选择** - 自动任务分析和最优模型路由
  - 支持deepseek-chat、deepseek-coder、deepseek-reasoner
  - 任务难度分析(简单、中等、复杂、专家级)
  - 基于任务特征自动匹配模型
  - 成本和性能优化
- 📊 **任务分析器** - 高级任务特征检测
  - 编程任务检测
  - 推理需求分析
  - 专家级主题识别
- 🎯 **智能模型路由** - 基于优先级的模型选择
  - deepseek-reasoner用于复杂推理和专家级任务
  - deepseek-coder用于编程任务
  - deepseek-chat用于一般对话

**文档:**
- [多模型选择指南](docs/manual/zh/model_selection.md)
- [模型选择配置](DEEPSEEK_MODELS.md)

### v0.3.1 - 内置技能
**发布日期**: 2026-01-29

**新功能:**
- ✨ **3个预装内置技能** - 即开即用
  - **text-processing** - 20+文本操作(大小写转换、提取邮箱/网址等)
  - **json-processor** - 8种JSON操作(解析、格式化、验证、提取、合并)
  - **data-analyzer** - 17种统计操作(均值、中位数、方差、分组等)
- ⚡ **自动预安装** - 启动时自动加载技能,无需配置
- 📦 **零依赖** - 纯Python实现,可离线工作
- 🔄 **视觉反馈** - 执行期间的加载动画和状态显示

**文档:**
- [内置技能参考](docs/BUILTIN_SKILLS.md)
- 所有操作的完整使用示例

### v0.3.0 - Agent技能系统
**发布日期**: 2026-01-29

**新功能:**
- ✨ **动态技能系统** - 按需扩展Alpha的能力
  - 自动发现和自动安装技能
  - 技能市场集成
  - 版本管理和依赖处理
- 🔍 **技能发现** - 搜索和浏览可用技能
- 📦 **技能管理** - 安装、更新和删除技能
- 🏪 **技能市场** - 访问社区贡献的技能
- 🎨 **CLI集成** - 新增`skills`和`search skill`命令

**架构:**
- AgentSkill基类用于创建自定义技能
- SkillRegistry用于生命周期管理
- SkillMarketplace用于发现
- SkillInstaller用于依赖处理
- SkillExecutor支持自动安装

**文档:**
- [Agent技能文档](docs/AGENT_SKILLS.md)
- [快速开始指南](docs/AGENT_SKILLS_QUICKSTART.md)
- [技能使用指南](docs/manual/zh/skills_guide.md)

### v0.2.0 - 任务调度与增强工具
**发布日期**: 2026-01-29

**新功能:**
- ✨ **任务调度器** - 支持cron表达式、间隔或一次性任务调度
- ✨ **HTTP工具** - 支持完整HTTP方法的API请求(GET, POST, PUT, DELETE)
- ✨ **日期时间工具** - 高级日期时间操作和时区支持
- ✨ **计算器工具** - 安全的数学计算和单位转换(长度、重量、温度、数据)
- 🔍 **增强搜索** - 通过DuckDuckGo API进行真实网络搜索
- 🎨 **更简洁界面** - 工具执行细节从聊天中隐藏(只显示结果)

**改进:**
- 支持多格式参数(JSON和YAML)
- 更好的错误处理和超时机制
- 改进的API配置和回退支持

### v0.1.1 - 多提供商支持
**发布日期**: 2026-01-29

**新功能:**
- ✨ **DeepSeek集成** - 性价比最高的AI提供商(便宜40-50倍)
- ✨ **多提供商系统** - 在DeepSeek、Claude和GPT-4之间轻松切换
- 🔧 **自定义API端点** - 支持自建或代理API

**改进:**
- 环境变量回退机制
- 改进的配置验证
- 更好的API错误提示

### v0.1.0 - 初始版本
**发布日期**: 2026-01-28

**核心功能:**
- 💬 交互式CLI聊天界面
- 🤖 AI驱动的任务执行
- 🔧 基础工具(Shell、File、Search)
- 🧠 对话记忆
- ⚡ 异步任务管理
- 📝 配置系统

## 故障排除

### "找不到模块"错误

确保您在虚拟环境中:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "API密钥未配置"错误

检查API密钥是否已设置:

```bash
# 检查哪些密钥已设置
echo $DEEPSEEK_API_KEY
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# 如果为空,导出您的密钥
export DEEPSEEK_API_KEY="您的密钥"
```

### 测试配置

```bash
# 检查API配置
./check_api_config.sh

# 测试DeepSeek连接
python test_deepseek.py
```

### 数据库错误

```bash
# 如果缺少数据目录,创建它
mkdir -p data

# 检查权限
ls -la data/
```

## 文档

### 用户指南
- [快速开始指南](docs/manual/zh/quickstart.md) - 5分钟上手
- [功能指南](docs/manual/zh/features.md) - 完整功能文档
- [模型选择指南](docs/manual/zh/model_selection.md) - 智能多模型选择
- [技能使用指南](docs/manual/zh/skills_guide.md) - 动态技能系统
- [API设置指南](docs/API_SETUP.md) - 配置AI提供商
- [工具使用指南](docs/TOOL_USAGE_GUIDE.md) - 如何使用各个工具

### 技术文档
- [Agent技能系统](docs/AGENT_SKILLS.md) - 技术文档
- [内置技能参考](docs/BUILTIN_SKILLS.md) - 预装技能
- [多模型选择](DEEPSEEK_MODELS.md) - DeepSeek模型配置

### API提供商指南
- [DeepSeek设置](docs/DEEPSEEK_GUIDE.md) - DeepSeek配置
- [Anthropic设置](docs/manual/zh/anthropic_config.md) - Claude配置

## 常见问题

**Q: 应该选择哪个AI提供商?**
A: 对于大多数用户,推荐使用DeepSeek,因为它性价比高且中文支持优秀。复杂编程任务可以使用Claude。

**Q: 可以在没有网络的情况下使用Alpha吗?**
A: Alpha需要网络连接来与AI提供商通信。部分工具(如计算器和日期时间)可以离线工作。

**Q: 我的数据安全吗?**
A: 所有对话都存储在本地的`data/alpha.db`中。API提供商(DeepSeek、Anthropic、OpenAI)会根据其隐私政策处理您的消息。

**Q: 可以安排重复性任务吗?**
A: 可以!使用cron表达式或基于间隔的调度。例如:"安排这个任务每周一上午10点运行"

**Q: 使用Alpha的成本是多少?**
A: Alpha本身是免费的。您只需支付API使用费用:
- DeepSeek: 每百万tokens约$0.42
- Claude: 每百万tokens约$18
- GPT-4: 每百万tokens约$20

## 获取帮助

- 📖 [文档](docs/)
- 🐛 [报告问题](https://github.com/flashspy/alpha/issues)
- 💬 [讨论区](https://github.com/flashspy/alpha/discussions)

## 许可证

MIT许可证 - 详见[LICENSE](LICENSE)文件

---

**当前版本**: v0.10.0
**状态**: 生产就绪 ✅
**最新功能**: 主动智能与自我进化(具有自主学习的高级AI能力)
**守护进程模式**: 可用(Linux/systemd)
**默认AI提供商**: DeepSeek(性价比最高)
