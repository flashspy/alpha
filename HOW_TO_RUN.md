# 🚀 Alpha AI Assistant - 运行指南

[English](#english) | [简体中文](#中文)

---

# <a name="中文"></a>简体中文

## 快速开始 (3步)

### 方法1: 使用运行脚本 (推荐) ⭐

```bash
# 1. 设置API密钥
export ANTHROPIC_AUTH_TOKEN="your-anthropic-api-key"

# 2. 运行
./run.sh
```

### 方法2: 使用快速启动脚本

```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
./start.sh
```

### 方法3: 手动启动

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 设置API密钥
export ANTHROPIC_AUTH_TOKEN="your-api-key"

# 3. 启动
python -m alpha.interface.cli
```

## 详细步骤

### 第一次运行

#### 1. 进入项目目录

```bash
cd /home/zhang/bot/alpha
```

#### 2. 创建虚拟环境 (如果还没有)

```bash
python3 -m venv venv
```

#### 3. 激活虚拟环境

```bash
source venv/bin/activate
```

你会看到命令提示符前面出现 `(venv)`:
```
(venv) user@host:~/projects/agents-7b5dad6160$
```

#### 4. 安装依赖 (如果还没有)

```bash
pip install -r requirements.txt
```

#### 5. 配置API密钥

**选项A: 使用环境变量 (推荐)**

```bash
# 推荐方式
export ANTHROPIC_AUTH_TOKEN="sk-ant-your-api-key-here"

# 或使用兼容方式
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"

# 可选: 自定义API端点
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

**选项B: 直接编辑配置文件**

```bash
# 编辑配置文件
nano config.yaml

# 或使用其他编辑器
vim config.yaml
```

修改以下部分:
```yaml
llm:
  default_provider: "anthropic"
  providers:
    anthropic:
      api_key: "sk-ant-your-actual-key-here"  # 直接填写API密钥
```

⚠️ **注意**: 直接在配置文件中填写密钥不安全，推荐使用环境变量。

#### 6. 启动Alpha

```bash
python -m alpha.interface.cli
```

或使用脚本:
```bash
./run.sh
```

### 成功启动后

你会看到类似这样的界面:

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              Alpha AI Assistant - Quick Start               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  ✓ ANTHROPIC_AUTH_TOKEN: sk-ant-api03-xxxx...
  ✓ ANTHROPIC_BASE_URL: (using default)

Starting Alpha AI Assistant...
Type 'help' for commands, 'quit' to exit

════════════════════════════════════════════════════════════════

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Alpha AI Assistant                                         ║
║   Type 'help' for commands, 'quit' to exit                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

You>
```

## 使用示例

### 基本对话

```
You> 你好

Alpha> 你好！我是Alpha AI助理。我可以帮你完成各种任务，
包括执行命令、操作文件、搜索信息等。有什么我可以帮助你的吗？
```

### 使用工具

#### 1. 执行Shell命令

```
You> 列出当前目录的文件

Alpha> TOOL: shell
PARAMS: {"command": "ls -la"}

Executing tool: shell
Tool succeeded: total 48
drwxr-xr-x 10 user staff  320 Jan 29 12:00 .
drwxr-xr-x  5 user staff  160 Jan 29 11:00 ..
-rw-r--r--  1 user staff 4096 Jan 29 12:00 README.md
...
```

#### 2. 文件操作

```
You> 创建一个test.txt文件，内容是"Hello Alpha"

Alpha> TOOL: file
PARAMS: {"operation": "write", "path": "test.txt", "content": "Hello Alpha"}

Executing tool: file
Tool succeeded: Written 11 bytes to test.txt

已创建文件test.txt！
```

#### 3. 查看系统状态

```
You> status

Alpha>
# System Status

- **Status**: running
- **Uptime**: 0:05:23
- **Tasks**: {'total': 0, 'running': 0, 'by_status': {...}}
- **Memory**: {'conversations': 5, 'tasks': 0, ...}
```

### 可用命令

在Alpha中输入以下命令:

| 命令 | 说明 |
|------|------|
| `help` | 显示帮助信息 |
| `status` | 查看系统状态 |
| `clear` | 清空对话历史 |
| `quit` 或 `exit` | 退出Alpha |

## 测试运行

### 快速测试

运行测试套件验证安装:

```bash
source venv/bin/activate
pytest tests/test_basic.py -v
```

应该看到:
```
============================= test session starts ==============================
...
tests/test_basic.py::test_event_bus PASSED                               [ 25%]
tests/test_basic.py::test_task_manager PASSED                            [ 50%]
tests/test_basic.py::test_memory_manager PASSED                          [ 75%]
tests/test_basic.py::test_tool_registry PASSED                           [100%]

============================== 4 passed in 2.14s ===============================
```

### 配置测试

测试配置加载:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

## 常见问题排查

### 问题1: 找不到模块

```
ModuleNotFoundError: No module named 'alpha'
```

**解决方法**:
```bash
# 确保在虚拟环境中
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### 问题2: API密钥错误

```
Error: No API key found!
```

**解决方法**:
```bash
# 检查环境变量
echo $ANTHROPIC_AUTH_TOKEN

# 如果为空，设置它
export ANTHROPIC_AUTH_TOKEN="your-key"
```

### 问题3: 数据库错误

```
Error: unable to open database file
```

**解决方法**:
```bash
# 创建数据目录
mkdir -p data logs
```

### 问题4: 端口已被占用

```
Error: Address already in use
```

**解决方法**:
```bash
# 这个错误只在API模式出现
# 修改config.yaml中的端口
interface:
  api:
    port: 8001  # 改为其他端口
```

### 问题5: 权限错误

```
Permission denied: ./run.sh
```

**解决方法**:
```bash
chmod +x run.sh
chmod +x start.sh
```

## 停止运行

### 正常退出

在Alpha提示符下输入:
```
You> quit
```

或按 `Ctrl + C`

### 强制停止

如果程序无响应:
```bash
# 按 Ctrl + C
# 或在另一个终端
ps aux | grep alpha
kill <process-id>
```

## 开发环境WSL中运行

### 在WSL中运行

```bash
# 1. 进入项目目录
cd /home/zhang/bot/alpha

# 2. 设置API密钥
export ANTHROPIC_AUTH_TOKEN="your-key"

# 3. 运行
./run.sh
```

### 部署到aliyun-vm测试环境

```bash
# 1. 打包项目
tar -czf alpha.tar.gz \
  alpha/ docs/ tests/ \
  requirements.txt config.example.yaml \
  README.md start.sh run.sh

# 2. 上传到服务器
scp alpha.tar.gz aliyun-vm:~/

# 3. SSH到服务器
ssh aliyun-vm

# 4. 解压并安装
tar -xzf alpha.tar.gz
cd alpha-*
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 配置并运行
export ANTHROPIC_AUTH_TOKEN="your-key"
./run.sh
```

## 后台运行

### 使用nohup

```bash
source venv/bin/activate
export ANTHROPIC_AUTH_TOKEN="your-key"
nohup python -m alpha.interface.cli > logs/alpha.log 2>&1 &

# 查看日志
tail -f logs/alpha.log
```

### 使用screen

```bash
# 创建新会话
screen -S alpha

# 在screen中运行
source venv/bin/activate
export ANTHROPIC_AUTH_TOKEN="your-key"
./run.sh

# 分离会话: 按 Ctrl+A 然后按 D

# 重新连接
screen -r alpha
```

### 使用tmux

```bash
# 创建新会话
tmux new -s alpha

# 运行Alpha
source venv/bin/activate
export ANTHROPIC_AUTH_TOKEN="your-key"
./run.sh

# 分离: 按 Ctrl+B 然后按 D

# 重新连接
tmux attach -t alpha
```

## 日志和调试

### 查看日志

```bash
# 实时查看日志
tail -f logs/alpha.log

# 查看最近的日志
tail -100 logs/alpha.log

# 搜索错误
grep ERROR logs/alpha.log
```

### 调试模式

编辑 `alpha/main.py`:

```python
# 修改日志级别
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG
    ...
)
```

## 性能监控

### 检查系统状态

在Alpha中:
```
You> status
```

### 检查资源使用

```bash
# CPU和内存
top -p $(pgrep -f alpha)

# 或使用htop
htop -p $(pgrep -f alpha)
```

## 下一步

运行成功后，你可以:

1. **阅读文档**: [功能详解](docs/zh/features.md)
2. **配置优化**: [Anthropic配置](docs/zh/anthropic_config.md)
3. **了解架构**: [架构设计](docs/zh/architecture.md)
4. **查看示例**: 尝试不同的工具和命令

---

**需要帮助?** 查看 [docs/zh/quickstart.md](docs/zh/quickstart.md) 或 [故障排查指南](#常见问题排查)

---

# <a name="english"></a>English

## Quick Start (3 Steps)

### Method 1: Using Run Script (Recommended) ⭐

```bash
# 1. Set API key
export ANTHROPIC_AUTH_TOKEN="your-anthropic-api-key"

# 2. Run
./run.sh
```

### Method 2: Using Quick Start Script

```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
./start.sh
```

### Method 3: Manual Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Set API key
export ANTHROPIC_AUTH_TOKEN="your-api-key"

# 3. Start
python -m alpha.interface.cli
```

## Detailed Steps

### First Time Running

#### 1. Enter Project Directory

```bash
cd /home/zhang/bot/alpha
```

#### 2. Create Virtual Environment (if not exists)

```bash
python3 -m venv venv
```

#### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

You'll see `(venv)` prefix in your prompt:
```
(venv) user@host:~/projects/agents-7b5dad6160$
```

#### 4. Install Dependencies (if not installed)

```bash
pip install -r requirements.txt
```

#### 5. Configure API Key

**Option A: Using Environment Variable (Recommended)**

```bash
# Recommended way
export ANTHROPIC_AUTH_TOKEN="sk-ant-your-api-key-here"

# Or compatible way
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"

# Optional: Custom API endpoint
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

**Option B: Edit Configuration File**

```bash
# Edit config file
nano config.yaml

# Or use other editor
vim config.yaml
```

Modify this section:
```yaml
llm:
  default_provider: "anthropic"
  providers:
    anthropic:
      api_key: "sk-ant-your-actual-key-here"  # Direct API key
```

⚠️ **Note**: Storing keys in config file is less secure. Environment variables recommended.

#### 6. Start Alpha

```bash
python -m alpha.interface.cli
```

Or use script:
```bash
./run.sh
```

### After Successful Start

You'll see an interface like this:

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              Alpha AI Assistant - Quick Start               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  ✓ ANTHROPIC_AUTH_TOKEN: sk-ant-api03-xxxx...
  ✓ ANTHROPIC_BASE_URL: (using default)

Starting Alpha AI Assistant...
Type 'help' for commands, 'quit' to exit

════════════════════════════════════════════════════════════════

You>
```

## Usage Examples

### Basic Conversation

```
You> Hello

Alpha> Hello! I'm Alpha AI Assistant. I can help you with various
tasks including executing commands, managing files, searching
information, and more. How can I help you?
```

### Using Tools

#### 1. Execute Shell Command

```
You> List files in current directory

Alpha> TOOL: shell
PARAMS: {"command": "ls -la"}

Executing tool: shell
Tool succeeded: total 48
drwxr-xr-x 10 user staff  320 Jan 29 12:00 .
...
```

#### 2. File Operations

```
You> Create a test.txt file with content "Hello Alpha"

Alpha> TOOL: file
PARAMS: {"operation": "write", "path": "test.txt", "content": "Hello Alpha"}

Executing tool: file
Tool succeeded: Written 11 bytes to test.txt

File test.txt created!
```

#### 3. Check System Status

```
You> status

Alpha>
# System Status

- **Status**: running
- **Uptime**: 0:05:23
- **Tasks**: {'total': 0, 'running': 0, ...}
- **Memory**: {'conversations': 5, ...}
```

### Available Commands

| Command | Description |
|---------|-------------|
| `help` | Show help information |
| `status` | Check system status |
| `clear` | Clear conversation history |
| `quit` or `exit` | Exit Alpha |

## Test Run

### Quick Test

Run test suite to verify installation:

```bash
source venv/bin/activate
pytest tests/test_basic.py -v
```

Should see:
```
============================= test session starts ==============================
...
tests/test_basic.py::test_event_bus PASSED                               [ 25%]
tests/test_basic.py::test_task_manager PASSED                            [ 50%]
tests/test_basic.py::test_memory_manager PASSED                          [ 75%]
tests/test_basic.py::test_tool_registry PASSED                           [100%]

============================== 4 passed in 2.14s ===============================
```

### Configuration Test

Test configuration loading:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

## Troubleshooting

See [Chinese section](#常见问题排查) for detailed troubleshooting guide.

## Next Steps

After successful run:

1. **Read Docs**: [Features Guide](docs/en/features.md)
2. **Configure**: [Anthropic Config](docs/en/anthropic_config.md)
3. **Learn Architecture**: [Architecture Design](docs/en/architecture.md)
4. **Try Examples**: Test different tools and commands

---

**Need Help?** See [docs/en/quickstart.md](docs/en/quickstart.md)
