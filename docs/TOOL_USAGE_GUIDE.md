# Alpha工具使用指南

## 设计理念

Alpha采用**通用工具组合**的设计理念，而不是为每个场景创建专用工具。这种设计有以下优势：

- ✅ 工具数量少，易于维护
- ✅ 更灵活，可以处理未预见的场景
- ✅ LLM可以自主决定如何组合使用工具
- ✅ 无需为每个新场景增加代码

## 核心工具

### 1. Search - 网页搜索
用途：查找信息、发现相关网站和API

```
TOOL: search
PARAMS: {"query": "北京天气预报 API"}
```

### 2. HTTP - 网络请求
用途：访问任何公开的API或网站

```
TOOL: http
PARAMS: {
  "url": "https://wttr.in/Beijing?format=j1",
  "method": "GET"
}
```

### 3. DateTime - 日期时间
用途：获取当前时间、时区转换、日期计算

```
TOOL: datetime
PARAMS: {"operation": "now", "timezone": "Asia/Shanghai"}
```

### 4. Calculator - 计算器
用途：数学计算、单位转换

```
TOOL: calculator
PARAMS: {"operation": "calculate", "expression": "25 * 4 + 10"}
```

### 5. File - 文件操作
用途：读取、写入、列出文件

```
TOOL: file
PARAMS: {"operation": "read", "path": "config.yaml"}
```

### 6. Shell - 命令执行
用途：执行系统命令

```
TOOL: shell
PARAMS: {"command": "ls -la"}
```

## 实际场景示例

### 场景1：查询天气

**用户请求：** "今天北京天气怎么样？"

**工具组合方案1 - 直接使用免费天气API：**
```
TOOL: http
PARAMS: {
  "url": "https://wttr.in/Beijing?format=j1&lang=zh-cn",
  "method": "GET"
}
```

**工具组合方案2 - 先搜索后访问：**
```
# 第一步：搜索天气API
TOOL: search
PARAMS: {"query": "北京天气 实时"}

# 第二步：访问找到的网站
TOOL: http
PARAMS: {"url": "https://www.weather.com.cn/weather/101010100.shtml"}
```

### 场景2：查询股票行情

**用户请求：** "今天股市行情如何？"

**推荐方案 - 搜索获取最新信息：**
```
TOOL: search
PARAMS: {"query": "今日股市行情 A股"}
```

**方案2 - 访问特定财经API（如果用户提供）：**
```
TOOL: http
PARAMS: {
  "url": "https://finance.sina.com.cn/realstock/company/sh000001/nc.shtml",
  "method": "GET"
}
```

### 场景3：新闻资讯

**用户请求：** "最新的AI新闻"

**方案：**
```
TOOL: search
PARAMS: {"query": "最新AI人工智能新闻 2026"}
```

### 场景4：汇率查询

**用户请求：** "美元对人民币汇率"

**方案1 - 使用免费汇率API：**
```
TOOL: http
PARAMS: {
  "url": "https://api.exchangerate-api.com/v4/latest/USD",
  "method": "GET"
}
```

**方案2 - 搜索获取：**
```
TOOL: search
PARAMS: {"query": "美元人民币汇率 今日"}
```

### 场景5：复杂任务 - 带日期的信息查询

**用户请求：** "今天有什么重要新闻？"

**工具组合：**
```
# 第一步：获取今天的日期
TOOL: datetime
PARAMS: {"operation": "now", "format": "YYYY-MM-DD"}

# 第二步：搜索今天的新闻
TOOL: search
PARAMS: {"query": "2026-01-29 重要新闻"}
```

## 常用免费API资源

### 天气API
- **wttr.in** - 免费天气API，支持全球城市
  ```
  https://wttr.in/{城市}?format=j1&lang=zh-cn
  ```

### 汇率API
- **exchangerate-api.com** - 免费汇率数据
  ```
  https://api.exchangerate-api.com/v4/latest/{货币代码}
  ```

### IP地理位置
- **ipapi.co** - IP地址查询
  ```
  https://ipapi.co/json/
  ```

### 公共数据
- **opendata** - 各类开放数据集
- **GitHub API** - 代码仓库信息

## LLM使用指南

作为Alpha的AI核心，在处理用户请求时：

1. **首选搜索** - 对于实时信息、新闻、动态数据，优先使用Search工具
2. **直接访问** - 当明确知道API地址时，使用HTTP工具直接获取
3. **工具组合** - 复杂任务可以组合多个工具（先搜索找资源，再HTTP获取详细信息）
4. **简化优先** - 能用一个工具解决的不用两个

## 添加新功能的方式

如果需要支持新的场景（如翻译、图片识别等）：

**不推荐：** 创建TranslateTool、ImageTool等专用工具

**推荐：**
1. 找到合适的免费API或服务
2. 在文档中记录API用法
3. LLM自动学会使用HTTP工具调用该API

这样无需修改代码即可扩展功能！

## 注意事项

1. **API限流** - 某些API有请求频率限制，注意合理使用
2. **数据时效性** - 搜索结果可能有延迟，关键数据建议直接访问权威API
3. **错误处理** - API请求失败时，可以降级使用Search工具
4. **隐私安全** - 不要发送敏感信息到第三方API
