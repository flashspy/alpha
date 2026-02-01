# Alpha 快速启动指南

## 方式1：推荐使用脚本（最简单）

```bash
# 启动服务器
./scripts/start_server.sh

# 连接聊天（新终端）
./scripts/start_client.sh
```

## 方式2：使用alpha命令

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 添加bin到PATH
export PATH="$PATH:$(pwd)/bin"

# 启动服务器
alpha start

# 连接聊天（新终端）
alpha chat
```

## 方式3：手动启动

```bash
# 启动服务器
source venv/bin/activate
python -m alpha.main --daemon --api-host 0.0.0.0 --api-port 8080

# 连接聊天（新终端）
source venv/bin/activate
python -m alpha.client.cli
```

## 使用systemd服务

```bash
# 安装服务
sudo ./scripts/install_daemon.sh

# 配置API密钥
sudo nano /etc/alpha/environment

# 启动服务
sudo systemctl start alpha

# 连接聊天
./scripts/start_client.sh
```

## 故障排查

### 依赖问题

如果遇到 `ModuleNotFoundError`，请确保在虚拟环境中安装了所有依赖：

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 服务器启动失败

查看日志：
```bash
tail -f logs/alpha.log
```

### 端口被占用

检查端口：
```bash
sudo lsof -i :8080
```

更改端口：
```bash
./scripts/start_server.sh 0.0.0.0 9000
```
