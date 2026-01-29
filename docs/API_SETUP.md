# Alpha API 配置指南

## 问题说明

如果您遇到以下错误：
```
Error: 400 Bad Request - This credential is only authorized for use with Claude Code
```

这说明您的API凭证是**Claude Code专用**，无法用于自定义客户端。

## 解决方案

### 方案1：使用官方Anthropic API（推荐）

1. **获取标准API密钥**
   - 访问：https://console.anthropic.com/
   - 创建一个标准API密钥（非Claude Code专用）

2. **配置环境变量**
   ```bash
   # 设置标准API密钥
   export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

   # 取消或删除Claude Code专用的base_url
   unset ANTHROPIC_BASE_URL
   # 或设置为官方地址
   export ANTHROPIC_BASE_URL="https://api.anthropic.com"
   ```

3. **重启Alpha**
   ```bash
   ./start.sh
   ```

### 方案2：混合使用（同时支持两种凭证）

如果您想保留moacode.org代理作为主要选择，但在失败时fallback到官方API：

```bash
# Claude Code专用凭证（用于moacode.org）
export ANTHROPIC_AUTH_TOKEN="your-claude-code-token"
export ANTHROPIC_BASE_URL="https://moacode.org"

# 标准API密钥（作为fallback）
export ANTHROPIC_API_KEY="sk-ant-api03-your-standard-key"
```

Alpha现在会：
1. 首先尝试使用ANTHROPIC_AUTH_TOKEN访问moacode.org
2. 如果失败（400/403错误），自动切换到官方API使用ANTHROPIC_API_KEY

## 测试配置

运行测试脚本验证配置：
```bash
python test_official_api.py
```

## 当前实现的Fallback机制

Alpha的LLM服务现在会自动处理：
- ✅ 检测400/403认证错误
- ✅ 自动尝试fallback到官方Anthropic API
- ✅ 记录切换日志（在logs/alpha.log中）
- ✅ 对用户透明（无需手动干预）

## 检查日志

如果遇到问题，检查日志文件：
```bash
tail -f logs/alpha.log
```

查找类似的信息：
```
WARNING - Request to https://moacode.org/v1/messages failed: ...
INFO - Falling back to official Anthropic API...
```
