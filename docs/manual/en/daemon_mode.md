# Daemon Mode - Running Alpha 24/7

[English](#english) | [简体中文](#简体中文)

---

# English

## Overview

Daemon Mode allows Alpha to run as a background service on Linux systems, providing true 24/7 operation. This mode is perfect for:

- **Continuous Operation**: Alpha runs in the background even after you log out
- **Automatic Startup**: Alpha starts automatically when your system boots
- **Auto-Recovery**: Alpha automatically restarts if it crashes
- **Scheduled Tasks**: Execute tasks on schedule without manual intervention
- **Production Deployment**: Run Alpha as a reliable system service

## Requirements

- Linux system with systemd (Ubuntu 16.04+, Debian 8+, CentOS 7+, etc.)
- Python 3.8 or higher
- Root/sudo access for installation
- Alpha installed on your system

## Quick Start

### 1. Install Daemon Service

```bash
# Run installation script
cd /path/to/alpha
sudo ./scripts/install_daemon.sh
```

This script will:
- Create a system user for Alpha
- Set up required directories
- Install systemd service file
- Create environment configuration file

### 2. Configure API Keys

Edit the environment configuration file:

```bash
sudo nano /etc/alpha/environment
```

Add your API keys:

```bash
# AI Provider API Keys
DEEPSEEK_API_KEY=your-deepseek-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here

# Logging
LOG_LEVEL=INFO
```

Save and exit (Ctrl+X, Y, Enter).

### 3. Start Alpha

```bash
sudo systemctl start alpha
```

### 4. Check Status

```bash
sudo systemctl status alpha
```

You should see:

```
● alpha.service - Alpha AI Assistant
   Loaded: loaded (/etc/systemd/system/alpha.service; enabled)
   Active: active (running) since...
   Main PID: 12345 (python)
```

## Managing Alpha Daemon

### Start Service

```bash
sudo systemctl start alpha
```

### Stop Service

```bash
sudo systemctl stop alpha
```

### Restart Service

```bash
sudo systemctl restart alpha
```

### Check Status

```bash
sudo systemctl status alpha
```

### Enable Auto-Start on Boot

```bash
sudo systemctl enable alpha
```

### Disable Auto-Start

```bash
sudo systemctl disable alpha
```

### Reload Configuration (Without Restart)

```bash
sudo systemctl reload alpha
# or
sudo kill -HUP $(systemctl show -p MainPID alpha | cut -d= -f2)
```

## Viewing Logs

### Recent Logs

```bash
sudo journalctl -u alpha -n 50
```

### Real-Time Logs (Follow Mode)

```bash
sudo journalctl -u alpha -f
```

### Logs from Specific Date

```bash
sudo journalctl -u alpha --since "2026-01-30"
sudo journalctl -u alpha --since "1 hour ago"
```

### Export Logs to File

```bash
sudo journalctl -u alpha > alpha-logs.txt
```

## Running Alpha Manually as Daemon

If you don't want to use systemd, you can run Alpha as a daemon manually:

```bash
# Start as daemon
python -m alpha.main --daemon --pid-file /tmp/alpha.pid

# Check if running
cat /tmp/alpha.pid

# Stop daemon
kill $(cat /tmp/alpha.pid)
```

## Troubleshooting

### Service Won't Start

1. Check logs for errors:

```bash
sudo journalctl -u alpha -n 100
```

2. Verify API keys are configured:

```bash
sudo cat /etc/alpha/environment
```

3. Check file permissions:

```bash
ls -la /opt/alpha
sudo chown -R alpha:alpha /opt/alpha
```

### Service Crashes or Restarts Frequently

1. Check error logs:

```bash
sudo journalctl -u alpha -p err
```

2. Verify restart count:

```bash
systemctl show -p NRestarts alpha
```

3. Check resource usage:

```bash
systemctl status alpha
```

### Configuration Reload Not Working

1. Check if SIGHUP handler is working:

```bash
sudo journalctl -u alpha | grep SIGHUP
```

2. Try manual signal:

```bash
sudo kill -HUP $(systemctl show -p MainPID alpha | cut -d= -f2)
```

## Uninstalling Daemon

To remove Alpha daemon:

```bash
sudo ./scripts/uninstall_daemon.sh
```

To completely remove Alpha (including files):

```bash
sudo ./scripts/uninstall_daemon.sh
sudo userdel alpha
sudo rm -rf /opt/alpha
sudo rm -rf /etc/alpha
```

## Advanced Configuration

### Custom Installation Directory

If Alpha is not installed at `/opt/alpha`, edit the service file:

```bash
sudo nano /etc/systemd/system/alpha.service
```

Update `WorkingDirectory` and paths, then reload:

```bash
sudo systemctl daemon-reload
```

### Resource Limits

Edit service file to adjust resource limits:

```bash
sudo nano /etc/systemd/system/alpha.service
```

Add or modify under `[Service]`:

```ini
# Memory limit
MemoryLimit=2G

# CPU quota (80% of one CPU)
CPUQuota=80%

# Max open files
LimitNOFILE=65536
```

Reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart alpha
```

### Custom Restart Policy

Adjust restart behavior in service file:

```ini
Restart=on-failure           # When to restart
RestartSec=10s               # Delay before restart
StartLimitInterval=60s       # Time window for restart attempts
StartLimitBurst=3            # Max restart attempts in interval
```

## Security Best Practices

1. **Run as Non-Root User**: Alpha daemon runs as the `alpha` user by default (recommended)

2. **Protect API Keys**:
   ```bash
   sudo chmod 640 /etc/alpha/environment
   sudo chown root:alpha /etc/alpha/environment
   ```

3. **Review Service Permissions**:
   ```bash
   sudo systemctl show alpha | grep -E 'User|Group'
   ```

4. **Monitor Logs Regularly**:
   ```bash
   sudo journalctl -u alpha -f
   ```

## See Also

- [Systemd Service Configuration](../systemd/README.md)
- [Alpha Features Guide](features.md)
- [API Setup Guide](../../docs/API_SETUP.md)

---

# 简体中文

## 概述

守护进程模式允许Alpha作为Linux系统的后台服务运行,实现真正的24/7运行。此模式适用于:

- **持续运行**: Alpha在后台运行,即使您注销后也继续工作
- **自动启动**: 系统启动时自动启动Alpha
- **自动恢复**: 如果Alpha崩溃,会自动重启
- **定时任务**: 按计划执行任务,无需手动干预
- **生产部署**: 将Alpha作为可靠的系统服务运行

## 系统要求

- 带有systemd的Linux系统 (Ubuntu 16.04+, Debian 8+, CentOS 7+等)
- Python 3.8或更高版本
- 安装时需要root/sudo权限
- 已安装Alpha

## 快速开始

### 1. 安装守护进程服务

```bash
# 运行安装脚本
cd /path/to/alpha
sudo ./scripts/install_daemon.sh
```

此脚本将:
- 创建Alpha的系统用户
- 设置所需目录
- 安装systemd服务文件
- 创建环境配置文件

### 2. 配置API密钥

编辑环境配置文件:

```bash
sudo nano /etc/alpha/environment
```

添加您的API密钥:

```bash
# AI服务商API密钥
DEEPSEEK_API_KEY=your-deepseek-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here

# 日志级别
LOG_LEVEL=INFO
```

保存并退出 (Ctrl+X, Y, Enter)。

### 3. 启动Alpha

```bash
sudo systemctl start alpha
```

### 4. 检查状态

```bash
sudo systemctl status alpha
```

您应该看到:

```
● alpha.service - Alpha AI Assistant
   Loaded: loaded (/etc/systemd/system/alpha.service; enabled)
   Active: active (running) since...
   Main PID: 12345 (python)
```

## 管理Alpha守护进程

### 启动服务

```bash
sudo systemctl start alpha
```

### 停止服务

```bash
sudo systemctl stop alpha
```

### 重启服务

```bash
sudo systemctl restart alpha
```

### 查看状态

```bash
sudo systemctl status alpha
```

### 启用开机自动启动

```bash
sudo systemctl enable alpha
```

### 禁用开机自动启动

```bash
sudo systemctl disable alpha
```

### 重新加载配置(无需重启)

```bash
sudo systemctl reload alpha
# 或
sudo kill -HUP $(systemctl show -p MainPID alpha | cut -d= -f2)
```

## 查看日志

### 最近日志

```bash
sudo journalctl -u alpha -n 50
```

### 实时日志(跟随模式)

```bash
sudo journalctl -u alpha -f
```

### 特定日期的日志

```bash
sudo journalctl -u alpha --since "2026-01-30"
sudo journalctl -u alpha --since "1 hour ago"
```

### 导出日志到文件

```bash
sudo journalctl -u alpha > alpha-logs.txt
```

## 手动以守护进程方式运行Alpha

如果不想使用systemd,可以手动以守护进程方式运行Alpha:

```bash
# 以守护进程方式启动
python -m alpha.main --daemon --pid-file /tmp/alpha.pid

# 检查是否运行
cat /tmp/alpha.pid

# 停止守护进程
kill $(cat /tmp/alpha.pid)
```

## 故障排查

### 服务无法启动

1. 检查日志中的错误:

```bash
sudo journalctl -u alpha -n 100
```

2. 验证API密钥是否配置:

```bash
sudo cat /etc/alpha/environment
```

3. 检查文件权限:

```bash
ls -la /opt/alpha
sudo chown -R alpha:alpha /opt/alpha
```

### 服务频繁崩溃或重启

1. 检查错误日志:

```bash
sudo journalctl -u alpha -p err
```

2. 验证重启次数:

```bash
systemctl show -p NRestarts alpha
```

3. 检查资源使用情况:

```bash
systemctl status alpha
```

### 配置重新加载不工作

1. 检查SIGHUP处理是否工作:

```bash
sudo journalctl -u alpha | grep SIGHUP
```

2. 尝试手动发送信号:

```bash
sudo kill -HUP $(systemctl show -p MainPID alpha | cut -d= -f2)
```

## 卸载守护进程

卸载Alpha守护进程:

```bash
sudo ./scripts/uninstall_daemon.sh
```

完全删除Alpha(包括文件):

```bash
sudo ./scripts/uninstall_daemon.sh
sudo userdel alpha
sudo rm -rf /opt/alpha
sudo rm -rf /etc/alpha
```

## 高级配置

### 自定义安装目录

如果Alpha不是安装在 `/opt/alpha`,编辑服务文件:

```bash
sudo nano /etc/systemd/system/alpha.service
```

更新 `WorkingDirectory` 和路径,然后重新加载:

```bash
sudo systemctl daemon-reload
```

### 资源限制

编辑服务文件以调整资源限制:

```bash
sudo nano /etc/systemd/system/alpha.service
```

在 `[Service]` 下添加或修改:

```ini
# 内存限制
MemoryLimit=2G

# CPU配额(一个CPU的80%)
CPUQuota=80%

# 最大打开文件数
LimitNOFILE=65536
```

重新加载并重启:

```bash
sudo systemctl daemon-reload
sudo systemctl restart alpha
```

### 自定义重启策略

在服务文件中调整重启行为:

```ini
Restart=on-failure           # 何时重启
RestartSec=10s               # 重启前延迟
StartLimitInterval=60s       # 重启尝试的时间窗口
StartLimitBurst=3            # 时间窗口内的最大重启次数
```

## 安全最佳实践

1. **以非root用户运行**: Alpha守护进程默认以 `alpha` 用户运行(推荐)

2. **保护API密钥**:
   ```bash
   sudo chmod 640 /etc/alpha/environment
   sudo chown root:alpha /etc/alpha/environment
   ```

3. **检查服务权限**:
   ```bash
   sudo systemctl show alpha | grep -E 'User|Group'
   ```

4. **定期监控日志**:
   ```bash
   sudo journalctl -u alpha -f
   ```

## 相关文档

- [Systemd服务配置](../systemd/README.md)
- [Alpha功能指南](features.md)
- [API设置指南](../../docs/API_SETUP.md)
