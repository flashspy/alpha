# 浏览器自动化指南

**Alpha 版本 0.7.0** | **阶段 4.3** | **最后更新: 2026-01-31**

---

## 概述

Alpha的浏览器自动化功能使AI助手能够与网页交互、自动化表单填写和智能提取数据。这个强大的功能允许Alpha通过Playwright库控制真实的浏览器来执行复杂的Web任务。

**主要优势:**
- 自动化Web浏览和导航
- 与网页元素交互(点击、填写表单、选择)
- 提取结构化数据和内容
- 捕获页面和元素截图
- 支持多种浏览器(Chromium、Firefox、WebKit)
- 安全的URL验证和操作控制
- 会话管理和资源清理

---

## 什么是浏览器自动化?

浏览器自动化是Alpha控制Web浏览器执行任务的能力。当您要求Alpha执行需要与网站交互的操作时,Alpha可以:

1. **启动浏览器** - 创建隔离的浏览器会话
2. **导航到页面** - 访问URL并等待加载
3. **验证安全性** - 检查URL和操作的安全性
4. **执行操作** - 点击、填写表单、提取数据
5. **捕获结果** - 截图、内容提取、状态报告
6. **清理资源** - 关闭浏览器并清理会话

这使Alpha能够处理以下任务:
- Web数据抓取和提取
- 表单自动填写和提交
- 网站自动化测试
- 页面监控和变更检测
- 截图捕获
- 结构化数据收集

---

## 何时使用

### 在以下情况使用浏览器自动化:

✅ **Web数据提取**
- 从网页抓取内容
- 提取结构化数据(表格、列表)
- 监控网站变更
- 收集多页面数据

✅ **表单自动化**
- 自动填写Web表单
- 提交数据到网站
- 自动化登录流程
- 批量表单处理

✅ **页面交互**
- 点击按钮和链接
- 导航多个页面
- 处理动态内容
- 与JavaScript应用交互

✅ **视觉捕获**
- 捕获页面截图
- 记录UI状态
- 视觉回归测试
- 创建文档截图

✅ **测试和监控**
- 自动化UI测试
- 监控网站可用性
- 验证页面功能
- 性能检查

### 当现有工具可用时不要使用:

❌ **简单HTTP请求** - 使用 `http` 工具
❌ **API调用** - 使用 `http` 工具直接调用API
❌ **静态内容下载** - 使用 `http` 工具
❌ **文件操作** - 使用 `file` 工具

**原则:** 只有当需要JavaScript渲染或交互式操作时才使用浏览器自动化。

---

## 支持的浏览器

### Chromium (Google Chrome)

**推荐用于:** 一般Web自动化

**优势:**
- 最广泛的兼容性
- 快速性能
- 优秀的开发工具
- 最常用的浏览器引擎

**示例:**
```yaml
action: navigate
browser: chromium
url: https://example.com
```

### Firefox

**推荐用于:** 隐私敏感任务

**优势:**
- 强隐私保护
- 良好的标准合规性
- 独特的渲染引擎
- 开源

**示例:**
```yaml
action: navigate
browser: firefox
url: https://example.com
```

### WebKit (Safari)

**推荐用于:** macOS/iOS兼容性测试

**优势:**
- Apple设备原生引擎
- 移动Safari行为
- 轻量级
- 独特的渲染特性

**示例:**
```yaml
action: navigate
browser: webkit
url: https://example.com
```

---

## 工作原理

浏览器自动化过程遵循具有安全检查的结构化管道:

```
┌─────────────────────────────────────────────────────────┐
│ 1. 会话创建                                              │
│    - 启动浏览器实例                                      │
│    - 创建隔离的浏览器上下文                              │
│    - 初始化页面                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. URL验证                                               │
│    - 检查URL格式和协议                                   │
│    - 验证黑名单                                          │
│    - 检查本地网络访问                                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 页面导航                                              │
│    - 导航到目标URL                                       │
│    - 等待页面加载完成                                    │
│    - 捕获页面状态                                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. 操作验证                                              │
│    - 验证操作参数                                        │
│    - 检查安全风险                                        │
│    - 请求用户批准(如需要)                                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 5. 操作执行                                              │
│    - 查找页面元素                                        │
│    - 执行交互(点击、填写等)                              │
│    - 等待操作完成                                        │
│    - 捕获截图(如需要)                                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 6. 结果返回                                              │
│    - 提取数据或内容                                      │
│    - 格式化结果                                          │
│    - 报告执行状态                                        │
│    - 清理会话(可选)                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 安全特性

Alpha的浏览器自动化系统将安全性作为首要任务进行设计:

### 1. URL验证

**含义:**
所有URL在导航前都经过严格验证。

**保护:**
- 协议验证(仅http/https)
- 黑名单检查
- 本地网络阻止
- 格式验证

**支持的协议:**
- `https://` - 加密连接(推荐)
- `http://` - 非加密连接(需批准)
- `file://` - 本地文件(默认禁用)

**被阻止的目标:**
- `localhost` 和 `127.0.0.1`
- 私有网络(10.x.x.x、192.168.x.x)
- 暗网地址(*.onion)
- 自定义黑名单中的域名

### 2. 会话隔离

**含义:**
每个浏览器会话在隔离的上下文中运行。

**保护:**
- 独立的cookie存储
- 分离的本地存储
- 隔离的缓存
- 会话间无数据泄露

**会话管理:**
- 自动超时清理
- 最大会话限制
- 资源使用跟踪
- 优雅的关闭处理

### 3. 操作验证

**含义:**
所有浏览器操作在执行前都经过验证。

**检查:**
- 参数验证
- 选择器格式检查
- 危险操作检测
- 脚本安全扫描

**需要批准的操作:**
- 表单数据提交
- JavaScript脚本执行
- 非HTTPS导航
- 上传文件

### 4. 资源限制

**会话限制:**
- **最大会话数:** 5个(可配置)
- **会话超时:** 5分钟不活动
- **内存使用:** 浏览器自动管理
- **磁盘空间:** 自动清理临时文件

**超时限制:**
- **页面加载:** 30秒(可配置)
- **元素等待:** 30秒(可配置)
- **操作执行:** 30秒(可配置)

### 5. 隐私保护

**默认设置:**
- 无持久化cookie
- 禁用缓存(可配置)
- 不保存浏览历史
- 会话后清理所有数据

**可配置选项:**
- 自定义User-Agent
- 隐身模式
- 禁用图片/JavaScript
- Cookie策略

---

## 入门指南

### 前提条件

使用浏览器自动化之前,请确保您拥有:

1. **已安装Playwright**
   ```bash
   # 安装Playwright
   pip install playwright

   # 安装浏览器
   python -m playwright install

   # 或仅安装Chromium
   python -m playwright install chromium
   ```

   **验证安装:**
   ```bash
   # 检查Playwright
   python -c "import playwright; print('Playwright installed')"

   # 检查浏览器
   python -m playwright install --help
   ```

2. **系统要求**
   - **Linux:** Ubuntu 18.04+, Debian 10+, CentOS 7+
   - **macOS:** 10.14+ (Mojave或更高)
   - **Windows:** Windows 10+

   **磁盘空间:**
   - Chromium: ~300 MB
   - Firefox: ~200 MB
   - WebKit: ~150 MB

3. **依赖项**
   ```bash
   # Linux可能需要额外的依赖
   # Ubuntu/Debian:
   sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1

   # CentOS/RHEL:
   sudo yum install nss atk at-spi2-atk cups-libs libdrm libXcomposite libXdamage libxkbcommon
   ```

### 配置

在 `config.yaml` 中启用浏览器自动化:

```yaml
browser_automation:
  enabled: true                    # 启用该功能

  defaults:
    browser: chromium              # 默认浏览器
    headless: true                 # 无头模式(无UI)
    timeout: 30                    # 默认超时(秒)

  viewport:
    width: 1920                    # 视口宽度
    height: 1080                   # 视口高度

  security:
    validate_urls: true            # 启用URL验证
    require_approval: true         # 需要用户批准
    allow_local_networks: false    # 阻止本地网络
    allow_file_access: false       # 阻止file://协议
    url_blacklist:                 # URL黑名单
      - "*.onion"
      - "localhost"
      - "127.0.0.1"

  actions:
    timeout: 30                    # 操作超时(秒)
    screenshot_on_error: true      # 错误时截图
    validate_before_action: true   # 执行前验证

  navigation:
    default_wait: load             # load, domcontentloaded, networkidle
    timeout: 30                    # 导航超时(秒)

  limits:
    max_sessions: 5                # 最大并发会话
    session_timeout: 300           # 会话超时(秒)

  screenshots:
    storage_path: /tmp/alpha/screenshots
    max_size_mb: 10                # 最大文件大小
    format: png                    # png, jpeg
    quality: 90                    # JPEG质量(1-100)
```

**配置选项说明:**

| 选项 | 默认值 | 描述 |
|-----|--------|-----|
| `enabled` | `false` | 启用/禁用浏览器自动化 |
| `defaults.browser` | `chromium` | 默认浏览器 |
| `defaults.headless` | `true` | 无头模式 |
| `defaults.timeout` | `30` | 默认超时(秒) |
| `viewport.width` | `1920` | 浏览器窗口宽度 |
| `viewport.height` | `1080` | 浏览器窗口高度 |
| `security.validate_urls` | `true` | 启用URL验证 |
| `security.require_approval` | `true` | 需要用户批准 |
| `security.allow_local_networks` | `false` | 允许访问本地网络 |
| `actions.timeout` | `30` | 操作超时(秒) |
| `navigation.default_wait` | `load` | 等待策略 |
| `limits.max_sessions` | `5` | 最大会话数 |

---

## 基本使用

### 示例1: 简单的页面导航

**您的请求:**
```
访问example.com并截图
```

**Alpha的响应:**
```
我将打开浏览器访问example.com并捕获截图。

TOOL: browser
ACTION: navigate
PARAMS:
  url: "https://example.com"
  wait_for: "load"
  take_screenshot: true

[安全检查: 通过]
[启动浏览器...]
[导航到: https://example.com]
[等待页面加载...]
[捕获截图...]

结果:
✓ 成功导航到 Example Domain
✓ 页面加载时间: 1.2秒
✓ 状态码: 200
✓ 截图已保存: /tmp/alpha/screenshots/example-com-20260131.png

页面信息:
- 标题: Example Domain
- URL: https://example.com/
- 加载状态: 完成
```

### 示例2: 点击元素

**您的请求:**
```
访问example.com并点击"More information"链接
```

**Alpha的响应:**
```
TOOL: browser
ACTION: click
PARAMS:
  url: "https://example.com"
  selector: "a:has-text('More information')"
  wait_after_click: "load"

[执行中...]

结果:
✓ 成功点击元素
✓ 导航到: https://www.iana.org/domains/reserved
✓ 页面标题: IANA — IANA-managed Reserved Domains
```

### 示例3: 提取页面内容

**您的请求:**
```
从example.com提取主要文本内容
```

**Alpha的响应:**
```
TOOL: browser
ACTION: extract_data
PARAMS:
  url: "https://example.com"
  selector: "body"
  extract_type: "text"

[执行中...]

提取的内容:
---
Example Domain

This domain is for use in illustrative examples in documents.
You may use this domain in literature without prior coordination or asking for permission.

More information...
---

提取信息:
- 字符数: 218
- 单词数: 32
- 提取时间: 0.8秒
```

### 示例4: 填写表单

**您的请求:**
```
在搜索表单中输入"Playwright"并提交
```

**Alpha的响应:**
```
TOOL: browser
ACTION: fill_form
PARAMS:
  url: "https://www.google.com"
  form_data:
    "input[name='q']": "Playwright"
  submit_selector: "input[type='submit']"

⚠️ 此操作将填写并提交表单。继续吗?
表单数据:
  - input[name='q']: Playwright

[y/N]: y

[执行中...]

结果:
✓ 表单已填写
✓ 表单已提交
✓ 导航到搜索结果页面
✓ 新页面标题: Playwright - Google Search
```

---

## 支持的操作

### 1. 导航操作

#### navigate - 导航到URL

**用途:** 访问网页

**参数:**
```yaml
action: navigate
url: string              # 必需: 目标URL
wait_for: string         # 可选: load, domcontentloaded, networkidle
timeout: integer         # 可选: 超时(秒)
```

**示例:**
```yaml
action: navigate
url: "https://github.com"
wait_for: "networkidle"
timeout: 30
```

**返回:**
- 成功/失败状态
- 最终URL(处理重定向)
- 页面标题
- HTTP状态码
- 加载时间

#### reload - 重新加载页面

**用途:** 刷新当前页面

**参数:**
```yaml
action: reload
wait_for: string         # 可选: 等待策略
```

**示例:**
```yaml
action: reload
wait_for: "load"
```

#### go_back - 后退

**用途:** 返回上一页

**参数:**
```yaml
action: go_back
wait_for: string         # 可选: 等待策略
```

#### go_forward - 前进

**用途:** 前进到下一页

**参数:**
```yaml
action: go_forward
wait_for: string         # 可选: 等待策略
```

### 2. 元素交互

#### click - 点击元素

**用途:** 点击页面元素

**参数:**
```yaml
action: click
selector: string         # 必需: CSS选择器
button: string           # 可选: left, right, middle
click_count: integer     # 可选: 点击次数(双击=2)
timeout: integer         # 可选: 超时(秒)
wait_after_click: string # 可选: 等待策略
```

**示例:**
```yaml
action: click
selector: "button.submit"
click_count: 1
wait_after_click: "load"
```

**选择器示例:**
```css
/* ID */
#element-id

/* Class */
.class-name

/* 标签 */
button

/* 属性 */
[data-testid="submit"]

/* 文本内容 */
button:has-text("Submit")

/* 组合 */
form.login button.submit
```

#### fill - 填写输入字段

**用途:** 在输入字段中输入文本

**参数:**
```yaml
action: fill
selector: string         # 必需: 输入字段选择器
value: string            # 必需: 要输入的文本
timeout: integer         # 可选: 超时(秒)
```

**示例:**
```yaml
action: fill
selector: "input[name='username']"
value: "myusername"
```

#### fill_form - 填写多个字段

**用途:** 一次填写整个表单

**参数:**
```yaml
action: fill_form
form_data: object        # 必需: 选择器到值的映射
submit_selector: string  # 可选: 提交按钮选择器
```

**示例:**
```yaml
action: fill_form
form_data:
  "input[name='email']": "user@example.com"
  "input[name='password']": "secretpass"
  "select[name='country']": "US"
submit_selector: "button[type='submit']"
```

#### select - 选择下拉选项

**用途:** 在select元素中选择选项

**参数:**
```yaml
action: select
selector: string         # 必需: select元素选择器
value: string           # 可选: 选项值
label: string           # 可选: 选项标签
index: integer          # 可选: 选项索引
```

**示例:**
```yaml
# 按值选择
action: select
selector: "select[name='country']"
value: "US"

# 按标签选择
action: select
selector: "select[name='country']"
label: "United States"

# 按索引选择
action: select
selector: "select[name='country']"
index: 0
```

#### check/uncheck - 复选框/单选框

**用途:** 选中或取消选中复选框

**参数:**
```yaml
action: check            # 或 uncheck
selector: string         # 必需: 复选框选择器
```

**示例:**
```yaml
action: check
selector: "input[type='checkbox'][name='agree']"
```

#### hover - 鼠标悬停

**用途:** 在元素上悬停鼠标

**参数:**
```yaml
action: hover
selector: string         # 必需: 元素选择器
timeout: integer         # 可选: 超时(秒)
```

**示例:**
```yaml
action: hover
selector: ".dropdown-menu"
```

#### upload_file - 上传文件

**用途:** 上传文件到文件输入

**参数:**
```yaml
action: upload_file
selector: string         # 必需: file input选择器
file_path: string        # 必需: 要上传的文件路径
```

**示例:**
```yaml
action: upload_file
selector: "input[type='file']"
file_path: "/path/to/document.pdf"
```

### 3. 数据提取

#### extract_data - 提取页面数据

**用途:** 从页面提取文本或数据

**参数:**
```yaml
action: extract_data
selector: string         # 可选: 元素选择器(默认: body)
extract_type: string     # 可选: text, html, attribute
attribute: string        # 可选: 属性名称(如果extract_type=attribute)
```

**示例:**
```yaml
# 提取文本
action: extract_data
selector: "h1"
extract_type: "text"

# 提取HTML
action: extract_data
selector: ".content"
extract_type: "html"

# 提取属性
action: extract_data
selector: "a.download"
extract_type: "attribute"
attribute: "href"
```

#### extract_table - 提取表格数据

**用途:** 提取HTML表格为结构化数据

**参数:**
```yaml
action: extract_table
selector: string         # 可选: 表格选择器(默认: table)
has_header: boolean      # 可选: 第一行是否为表头
```

**示例:**
```yaml
action: extract_table
selector: "table.data"
has_header: true
```

**返回格式:**
```json
{
  "headers": ["Name", "Age", "City"],
  "rows": [
    ["Alice", "30", "New York"],
    ["Bob", "25", "London"]
  ]
}
```

#### extract_links - 提取所有链接

**用途:** 提取页面上的所有链接

**参数:**
```yaml
action: extract_links
selector: string         # 可选: 容器选择器
```

**示例:**
```yaml
action: extract_links
selector: "nav.main-menu"
```

**返回格式:**
```json
[
  {"text": "Home", "href": "/"},
  {"text": "About", "href": "/about"},
  {"text": "Contact", "href": "/contact"}
]
```

### 4. 截图和视觉

#### screenshot - 捕获截图

**用途:** 捕获页面或元素截图

**参数:**
```yaml
action: screenshot
selector: string         # 可选: 元素选择器(默认: 整页)
full_page: boolean       # 可选: 整页截图(默认: true)
format: string           # 可选: png, jpeg
quality: integer         # 可选: JPEG质量(1-100)
```

**示例:**
```yaml
# 整页截图
action: screenshot
full_page: true
format: "png"

# 元素截图
action: screenshot
selector: ".chart"
format: "jpeg"
quality: 90
```

### 5. 等待操作

#### wait_for_selector - 等待元素出现

**用途:** 等待元素在页面上可见

**参数:**
```yaml
action: wait_for_selector
selector: string         # 必需: 元素选择器
state: string            # 可选: visible, hidden, attached
timeout: integer         # 可选: 超时(秒)
```

**示例:**
```yaml
action: wait_for_selector
selector: ".loading-spinner"
state: "hidden"
timeout: 30
```

**状态选项:**
- `visible` - 元素可见
- `hidden` - 元素隐藏
- `attached` - 元素附加到DOM

#### wait_for_url - 等待URL匹配

**用途:** 等待URL更改

**参数:**
```yaml
action: wait_for_url
url_pattern: string      # 必需: URL模式或正则
timeout: integer         # 可选: 超时(秒)
```

**示例:**
```yaml
action: wait_for_url
url_pattern: "**/search?*"
timeout: 10
```

### 6. 高级操作

#### execute_script - 执行JavaScript

**用途:** 在页面上下文中运行JavaScript

**参数:**
```yaml
action: execute_script
script: string           # 必需: JavaScript代码
args: array              # 可选: 脚本参数
```

**示例:**
```yaml
action: execute_script
script: |
  return document.title;

# 带参数
action: execute_script
script: |
  const [selector] = arguments;
  return document.querySelector(selector).textContent;
args: ["h1"]
```

**⚠️ 安全警告:** 此操作需要用户批准并进行安全扫描。

#### scroll - 滚动页面

**用途:** 滚动页面或元素

**参数:**
```yaml
action: scroll
selector: string         # 可选: 元素选择器
direction: string        # 可选: up, down, left, right
amount: integer          # 可选: 滚动量(像素)
to_bottom: boolean       # 可选: 滚动到底部
```

**示例:**
```yaml
# 滚动到底部
action: scroll
to_bottom: true

# 滚动特定量
action: scroll
direction: "down"
amount: 500
```

#### press_key - 按键

**用途:** 模拟键盘按键

**参数:**
```yaml
action: press_key
selector: string         # 可选: 元素选择器
key: string              # 必需: 键名(Enter, Escape, ArrowDown等)
```

**示例:**
```yaml
# 按Enter
action: press_key
selector: "input.search"
key: "Enter"

# 按Escape
action: press_key
key: "Escape"
```

**常用键名:**
- `Enter`
- `Escape`
- `ArrowDown`, `ArrowUp`, `ArrowLeft`, `ArrowRight`
- `Tab`
- `Backspace`
- `Delete`

---

## 配置选项

### 完整配置参考

```yaml
browser_automation:
  # 功能开关
  enabled: true

  # 默认设置
  defaults:
    browser: chromium              # chromium, firefox, webkit
    headless: true                 # 无头模式
    timeout: 30                    # 默认超时(秒)
    locale: "en-US"                # 浏览器语言
    timezone: "America/New_York"   # 时区

  # 视口大小
  viewport:
    width: 1920
    height: 1080

  # 安全设置
  security:
    validate_urls: true            # URL验证
    require_approval: true         # 需要用户批准
    allow_local_networks: false    # 允许本地网络
    allow_file_access: false       # 允许file://
    url_blacklist:                 # URL黑名单
      - "*.onion"                  # Tor网站
      - "localhost"                # 本地主机
      - "127.0.0.1"                # 回环地址
      - "*.internal"               # 内部域名

  # 操作设置
  actions:
    timeout: 30                    # 操作超时(秒)
    screenshot_on_error: true      # 错误时截图
    validate_before_action: true   # 执行前验证

  # 导航设置
  navigation:
    default_wait: load             # load, domcontentloaded, networkidle
    timeout: 30                    # 导航超时(秒)
    max_redirects: 10              # 最大重定向次数

  # 会话限制
  limits:
    max_sessions: 5                # 最大并发会话
    session_timeout: 300           # 会话超时(秒)
    max_pages_per_session: 10      # 每会话最大页面数

  # 截图设置
  screenshots:
    storage_path: /tmp/alpha/screenshots
    max_size_mb: 10                # 最大文件大小(MB)
    format: png                    # png, jpeg
    quality: 90                    # JPEG质量
    auto_cleanup: true             # 自动清理旧截图
    retention_days: 7              # 保留天数

  # 性能优化
  performance:
    disable_images: false          # 禁用图片加载
    disable_javascript: false      # 禁用JavaScript
    disable_css: false             # 禁用CSS
    cache_enabled: false           # 启用缓存

  # 代理设置
  proxy:
    enabled: false
    server: "http://proxy.example.com:8080"
    username: ""
    password: ""
```

### 常见配置场景

#### 1. 快速数据抓取

**优化速度,最小资源使用:**

```yaml
browser_automation:
  defaults:
    browser: chromium
    headless: true

  performance:
    disable_images: true           # 跳过图片
    disable_css: true              # 跳过CSS
    cache_enabled: false

  navigation:
    default_wait: domcontentloaded # 更快的等待
```

#### 2. 完整页面测试

**完整渲染和交互:**

```yaml
browser_automation:
  defaults:
    browser: chromium
    headless: false                # 显示浏览器

  viewport:
    width: 1920
    height: 1080

  performance:
    disable_images: false
    disable_javascript: false

  navigation:
    default_wait: networkidle      # 等待所有网络请求
```

#### 3. 移动设备模拟

**模拟移动浏览器:**

```yaml
browser_automation:
  defaults:
    browser: chromium
    headless: true
    user_agent: "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)"

  viewport:
    width: 375                     # iPhone宽度
    height: 667                    # iPhone高度
```

#### 4. 高安全模式

**最严格的安全设置:**

```yaml
browser_automation:
  security:
    validate_urls: true
    require_approval: true
    allow_local_networks: false
    allow_file_access: false
    url_blacklist:
      - "*.onion"
      - "localhost"
      - "127.0.0.1"
      - "10.*.*.*"
      - "192.168.*.*"
      - "172.16.*.*"

  actions:
    validate_before_action: true
```

---

## 故障排查

### 常见问题

#### 1. "Playwright未安装"

**问题:** Playwright库未安装或浏览器未下载。

**解决方案:**
```bash
# 安装Playwright
pip install playwright

# 安装浏览器
python -m playwright install

# 验证
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

#### 2. "浏览器启动失败"

**问题:** 浏览器无法启动。

**原因和解决方案:**

**Linux - 缺少依赖:**
```bash
# Ubuntu/Debian
sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1

# CentOS/RHEL
sudo yum install nss atk at-spi2-atk
```

**权限问题:**
```bash
# 检查Playwright安装目录权限
ls -la ~/.cache/ms-playwright/

# 修复权限
chmod -R 755 ~/.cache/ms-playwright/
```

**无头模式问题:**
```yaml
# 尝试非无头模式
defaults:
  headless: false
```

#### 3. "导航超时"

**问题:** 页面加载超过超时时间。

**解决方案:**

**增加超时:**
```yaml
navigation:
  timeout: 60                      # 增加到60秒
```

**更改等待策略:**
```yaml
navigation:
  default_wait: domcontentloaded  # 不等待所有资源
```

**禁用资源:**
```yaml
performance:
  disable_images: true             # 跳过图片加载
```

#### 4. "元素未找到"

**问题:** 选择器找不到元素。

**调试步骤:**

1. **验证选择器:**
   ```yaml
   # 使用更宽松的选择器
   selector: "button"               # 而不是 "button.specific-class"
   ```

2. **等待元素出现:**
   ```yaml
   action: wait_for_selector
   selector: "button.submit"
   state: "visible"
   timeout: 30
   ```

3. **检查iframe:**
   ```yaml
   # 元素可能在iframe中
   # Playwright自动处理iframe,但可能需要更长时间
   timeout: 60
   ```

4. **捕获截图调试:**
   ```yaml
   action: screenshot
   full_page: true
   # 查看页面实际状态
   ```

#### 5. "会话已过期"

**问题:** 会话在操作前过期。

**解决方案:**
```yaml
limits:
  session_timeout: 600             # 增加到10分钟
```

#### 6. "URL被阻止"

**问题:** URL在黑名单中或是本地地址。

**解决方案:**

**允许本地网络(谨慎使用):**
```yaml
security:
  allow_local_networks: true
```

**从黑名单移除:**
```yaml
security:
  url_blacklist:
    - "*.onion"                    # 只保留必要的
```

#### 7. "截图保存失败"

**问题:** 无法保存截图文件。

**解决方案:**

**检查目录权限:**
```bash
# 创建目录
mkdir -p /tmp/alpha/screenshots

# 设置权限
chmod 755 /tmp/alpha/screenshots
```

**检查磁盘空间:**
```bash
df -h /tmp
```

**调整配置:**
```yaml
screenshots:
  storage_path: /home/user/alpha/screenshots  # 使用可写位置
  max_size_mb: 5                    # 减小最大大小
```

#### 8. "内存不足"

**问题:** 浏览器占用过多内存。

**解决方案:**

**减少并发会话:**
```yaml
limits:
  max_sessions: 2                  # 减少最大会话数
```

**启用资源限制:**
```yaml
performance:
  disable_images: true
  cache_enabled: false
```

**定期清理会话:**
```yaml
limits:
  session_timeout: 180             # 3分钟后清理
```

---

## 最佳实践

### 1. 安全性

✅ **应该:**
- 始终启用URL验证
- 保持批准启用用于敏感操作
- 审查将访问的URL
- 使用HTTPS URL
- 定期审查黑名单
- 最小化本地网络访问

❌ **不应该:**
- 禁用所有安全检查
- 盲目批准操作
- 访问不受信任的网站
- 允许不受限制的脚本执行
- 在表单中共享敏感数据
- 访问本地网络资源

### 2. 性能

✅ **应该:**
- 使用适当的等待策略
- 为快速抓取禁用不需要的资源
- 重用会话进行多个操作
- 设置合理的超时
- 在完成后清理会话
- 使用选择性截图

❌ **不应该:**
- 使用不必要的长超时
- 为简单页面等待networkidle
- 创建过多并发会话
- 保持会话空闲
- 捕获不必要的整页截图
- 在非无头模式下运行生产任务

### 3. 选择器策略

✅ **应该:**
- 使用特定、稳定的选择器
- 优先使用data-testid属性
- 使用文本内容进行可读性
- 测试选择器的健壮性
- 为动态内容添加等待
- 使用语义HTML选择器

❌ **不应该:**
- 依赖脆弱的class名称
- 使用过于复杂的选择器
- 假设元素立即可用
- 使用绝对XPath
- 忽略iframe上下文
- 硬编码索引位置

**好的选择器示例:**
```css
/* 优秀: 使用测试ID */
[data-testid="submit-button"]

/* 良好: 语义+文本 */
button:has-text("Submit")

/* 良好: 语义+属性 */
input[type="email"][name="user-email"]

/* 可以: Class+类型 */
button.primary

/* 避免: 仅依赖位置 */
div > div > button:nth-child(3)
```

### 4. 错误处理

✅ **应该:**
- 错误时捕获截图
- 仔细阅读错误消息
- 实现重试逻辑
- 验证前置条件
- 优雅地处理超时
- 记录失败以供调试

❌ **不应该:**
- 忽略错误
- 无限重试
- 假设页面状态
- 跳过验证
- 隐藏错误详情
- 第一次失败就放弃

### 5. 数据提取

✅ **应该:**
- 验证提取的数据
- 处理缺失元素
- 使用结构化提取
- 清理和格式化数据
- 验证数据完整性
- 处理动态内容

❌ **不应该:**
- 假设元素存在
- 忽略数据验证
- 过度提取不需要的数据
- 忽略错误的提取
- 跳过数据清理
- 硬编码数据结构

### 6. 会话管理

✅ **应该:**
- 为相关任务重用会话
- 完成后关闭会话
- 监控会话数量
- 设置适当的超时
- 处理会话过期
- 清理资源

❌ **不应该:**
- 为每个操作创建新会话
- 使会话无限期打开
- 超过最大会话限制
- 忽略超时
- 泄漏会话资源
- 跳过清理

---

## 示例库

### 示例1: 简单数据抓取

**任务:** 从网页提取标题和主要内容

**代码:**
```python
# Alpha将执行以下操作:
action = {
    "action": "navigate",
    "url": "https://example.com/article",
    "wait_for": "load"
}

# 然后提取数据
extract = {
    "action": "extract_data",
    "targets": {
        "title": "h1",
        "content": "article.main-content",
        "author": ".author-name"
    },
    "extract_type": "text"
}
```

**结果:**
```json
{
  "title": "Understanding Web Automation",
  "content": "Web automation is the process of...",
  "author": "John Doe"
}
```

### 示例2: 表单提交

**任务:** 登录到网站

**代码:**
```python
# 导航到登录页面
navigate = {
    "action": "navigate",
    "url": "https://example.com/login"
}

# 填写表单
fill_form = {
    "action": "fill_form",
    "form_data": {
        "input[name='username']": "myuser",
        "input[name='password']": "mypass"
    },
    "submit_selector": "button[type='submit']"
}

# 等待重定向
wait = {
    "action": "wait_for_url",
    "url_pattern": "**/dashboard",
    "timeout": 10
}
```

### 示例3: 表格数据提取

**任务:** 从HTML表格提取数据

**代码:**
```python
# 导航到数据页面
navigate = {
    "action": "navigate",
    "url": "https://example.com/data"
}

# 提取表格
extract_table = {
    "action": "extract_table",
    "selector": "table.data-table",
    "has_header": True
}
```

**结果:**
```json
{
  "headers": ["Name", "Age", "City"],
  "rows": [
    ["Alice", "30", "New York"],
    ["Bob", "25", "London"],
    ["Charlie", "35", "Paris"]
  ]
}
```

### 示例4: 动态内容等待

**任务:** 等待AJAX加载完成后提取内容

**代码:**
```python
# 导航到页面
navigate = {
    "action": "navigate",
    "url": "https://example.com/dynamic"
}

# 等待加载指示器消失
wait = {
    "action": "wait_for_selector",
    "selector": ".loading-spinner",
    "state": "hidden",
    "timeout": 30
}

# 等待内容出现
wait_content = {
    "action": "wait_for_selector",
    "selector": ".dynamic-content",
    "state": "visible"
}

# 提取内容
extract = {
    "action": "extract_data",
    "selector": ".dynamic-content",
    "extract_type": "text"
}
```

### 示例5: 多页面导航

**任务:** 导航多个页面并收集数据

**代码:**
```python
# 第1页
page1 = {
    "action": "navigate",
    "url": "https://example.com/page1"
}

extract1 = {
    "action": "extract_data",
    "selector": ".content"
}

# 点击下一页
click_next = {
    "action": "click",
    "selector": "a.next-page",
    "wait_after_click": "load"
}

# 第2页提取
extract2 = {
    "action": "extract_data",
    "selector": ".content"
}
```

### 示例6: 截图比较

**任务:** 捕获并比较页面截图

**代码:**
```python
# 捕获初始状态
screenshot1 = {
    "action": "screenshot",
    "full_page": True,
    "path": "/tmp/before.png"
}

# 执行操作(点击按钮)
click = {
    "action": "click",
    "selector": "button.toggle"
}

# 捕获更改后状态
screenshot2 = {
    "action": "screenshot",
    "full_page": True,
    "path": "/tmp/after.png"
}

# Alpha可以比较两个截图以检测变化
```

### 示例7: 文件下载

**任务:** 触发文件下载

**代码:**
```python
# 导航到下载页面
navigate = {
    "action": "navigate",
    "url": "https://example.com/downloads"
}

# 点击下载按钮
# 注意: Playwright自动处理下载
click_download = {
    "action": "click",
    "selector": "a.download-link"
}

# 提取下载链接而不是点击
extract_link = {
    "action": "extract_data",
    "selector": "a.download-link",
    "extract_type": "attribute",
    "attribute": "href"
}
```

### 示例8: 无限滚动

**任务:** 滚动加载所有内容

**代码:**
```python
# 导航到页面
navigate = {
    "action": "navigate",
    "url": "https://example.com/infinite-scroll"
}

# 多次滚动到底部
for i in range(5):
    scroll = {
        "action": "scroll",
        "to_bottom": True
    }

    # 等待新内容加载
    wait = {
        "action": "wait",
        "duration": 2  # 等待2秒
    }

# 提取所有加载的内容
extract = {
    "action": "extract_data",
    "selector": ".content-item",
    "extract_type": "text"
}
```

---

## 高级用法

### 1. 自定义User-Agent

**用途:** 模拟不同的浏览器或设备

**配置:**
```yaml
defaults:
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

**动态设置:**
```python
session_config = {
    "user_agent": "Custom Bot 1.0"
}
```

### 2. Cookie管理

**保存cookies:**
```python
# 登录后
save_cookies = {
    "action": "get_cookies"
}
# 结果: [{"name": "session", "value": "abc123", ...}]
```

**加载cookies:**
```python
# 在新会话中
load_cookies = {
    "action": "set_cookies",
    "cookies": [
        {"name": "session", "value": "abc123", "domain": "example.com"}
    ]
}
```

### 3. 地理定位

**设置位置:**
```yaml
# 在会话配置中
geolocation:
  latitude: 40.7128
  longitude: -74.0060
permissions:
  - geolocation
```

### 4. 网络拦截

**阻止资源:**
```python
# 阻止广告和跟踪器
block_resources = {
    "action": "block_urls",
    "patterns": [
        "**/ads/**",
        "**/*.doubleclick.net/**",
        "**/analytics.js"
    ]
}
```

### 5. 请求拦截

**修改请求:**
```python
# 添加自定义header
intercept = {
    "action": "set_extra_headers",
    "headers": {
        "Authorization": "Bearer token123",
        "X-Custom-Header": "value"
    }
}
```

### 6. 响应等待

**等待特定响应:**
```python
# 等待API调用完成
wait_response = {
    "action": "wait_for_response",
    "url_pattern": "**/api/data",
    "timeout": 30
}
```

### 7. 多个上下文

**隔离会话:**
```python
# 会话1: 用户A
session1 = {
    "session_id": "user-a",
    "cookies": [...]
}

# 会话2: 用户B
session2 = {
    "session_id": "user-b",
    "cookies": [...]
}
```

### 8. PDF生成

**保存页面为PDF:**
```python
generate_pdf = {
    "action": "pdf",
    "path": "/tmp/page.pdf",
    "format": "A4",
    "print_background": True
}
```

---

## 限制

### 当前限制

1. **单页面操作**
   - 每个会话一次操作一个页面
   - 多标签页需要额外处理
   - 解决方法: 使用多个会话

2. **JavaScript执行限制**
   - 有安全扫描
   - 需要用户批准
   - 解决方法: 使用内置操作

3. **下载处理**
   - 自动下载处理有限
   - 需要手动管理下载
   - 解决方法: 提取下载链接

4. **认证**
   - 无内置OAuth处理
   - 需要手动cookie管理
   - 解决方法: 使用fill_form进行基本认证

5. **性能**
   - 浏览器启动需要时间
   - 资源密集型
   - 解决方法: 重用会话,启用无头模式

6. **网络**
   - 无内置代理轮换
   - 基本代理支持
   - 解决方法: 配置外部代理

### 计划增强

未来版本将包括:
- 多标签页支持
- 高级下载管理
- 内置OAuth流程
- 代理轮换
- 请求/响应拦截API
- WebSocket支持
- Service Worker处理
- 视频录制
- 性能分析

---

## 常见问题

### 一般问题

**问: 浏览器自动化安全吗?**

答: 正确使用时是安全的。所有URL和操作都经过验证,会话是隔离的,并且有用户批准选项。但是,您应该始终在批准前审查将访问的URL和执行的操作。

**问: 我需要了解编程才能使用此功能吗?**

答: 不需要!您用自然语言描述您想要什么,Alpha会生成和执行浏览器操作。但是,基本的HTML/CSS知识有助于理解选择器。

**问: 无头模式是什么?**

答: 无头模式在没有可见UI的情况下运行浏览器。它更快、占用资源更少,是自动化的推荐模式。设置 `headless: false` 可以看到浏览器窗口。

**问: 我可以自动化需要登录的网站吗?**

答: 可以,使用 `fill_form` 操作输入凭据。但是,要小心敏感数据。考虑使用cookie来维护会话而不是重复登录。

**问: 为什么我的选择器不工作?**

答: 常见原因:
- 元素在iframe中
- 元素是动态加载的(需要等待)
- 选择器拼写错误
- 页面结构已更改
尝试捕获截图以调试页面状态。

### 功能相关问题

**问: 我可以在单个会话中访问多个页面吗?**

答: 可以!一旦创建会话,您可以导航到多个URL、点击链接并执行多个操作,而无需重新创建会话。

**问: 如何处理CAPTCHA?**

答: CAPTCHA专门设计用于阻止自动化。选项:
- 使用需要CAPTCHA解决服务的API
- 手动解决CAPTCHA(非无头模式)
- 避免触发CAPTCHA(慢速请求,真实User-Agent)

**问: 我可以自动化文件上传吗?**

答: 可以,使用 `upload_file` 操作。文件必须在服务器上存在可访问。

**问: 如何提取动态加载的内容?**

答: 使用 `wait_for_selector` 等待内容出现后再提取。对于无限滚动,使用 `scroll` 操作触发加载。

**问: 我可以运行并行会话吗?**

答: 可以,最多为 `max_sessions` 限制(默认5)。每个会话是独立的并且有自己的状态。

**问: 如何检测页面上的变化?**

答: 捕获截图之前和之后,或定期提取内容并比较。Alpha可以帮助检测差异。

### 性能问题

**问: 为什么浏览器启动很慢?**

答: 首次启动需要时间来初始化Playwright和浏览器。后续操作使用同一会话会更快。考虑重用会话进行多个操作。

**问: 如何加快页面加载?**

答:
- 使用 `domcontentloaded` 而不是 `load`
- 禁用图片: `disable_images: true`
- 禁用CSS: `disable_css: true`
- 使用更快的浏览器: Chromium通常最快

**问: 浏览器占用太多内存吗?**

答: 浏览器是资源密集型的。要减少使用:
- 减少 `max_sessions`
- 启用 `session_timeout` 以自动清理
- 在完成后关闭会话
- 使用 `headless: true`

### 安全问题

**问: 自动化可以损害我的系统吗?**

答: Alpha的浏览器自动化在隔离的上下文中运行,具有URL验证和操作控制。风险很小,但始终:
- 审查将访问的URL
- 谨慎批准操作
- 避免访问不受信任的网站

**问: 我的凭据安全吗?**

答: 凭据在内存中处理并且不记录。但是:
- 不要在配置文件中硬编码凭据
- 使用环境变量
- 考虑使用cookie而不是重复登录
- 启用 `require_approval` 进行表单填写

**问: 我可以访问内部网站吗?**

答: 默认情况下,本地网络被阻止。要允许:
```yaml
security:
  allow_local_networks: true
```
⚠️ **警告:** 仅对受信任的任务启用此功能。

**问: 截图存储在哪里?**

答: 在 `screenshots.storage_path` 中(默认: `/tmp/alpha/screenshots`)。如果 `auto_cleanup: true`,则会在 `retention_days` 后删除。

---

## 获取帮助

### 资源

- **用户指南:** 本文档
- **API参考:** `/docs/internal/browser_automation_api.md`
- **架构:** `/docs/internal/phase4_3_browser_automation_plan.md`
- **配置:** `/config.yaml`
- **Playwright文档:** https://playwright.dev/python/

### 支持

如果遇到问题:

1. **查看本指南的故障排查部分**
2. **仔细查看错误消息**
3. **捕获截图以调试页面状态**
4. **验证配置设置**
5. **检查Playwright安装**
6. **测试简单页面(如example.com)**

### 反馈

您的反馈有助于改进Alpha:
- 报告错误和问题
- 建议功能增强
- 分享使用案例和示例
- 为文档做出贡献

---

## 版本历史

### 版本0.7.0(当前)
- 浏览器自动化系统的初始版本
- 支持Chromium、Firefox和WebKit
- 基于Playwright的自动化
- 全面的操作集(导航、交互、提取)
- URL和操作验证
- 会话管理和清理
- 截图捕获
- 用户批准工作流

### 即将推出的功能
- 多标签页支持
- 高级下载管理
- OAuth流程处理
- 代理轮换
- 视频录制
- 性能分析
- WebSocket支持

---

## 附录

### A. CSS选择器速查表

**基本选择器:**
```css
/* 标签 */
div, p, button, input

/* ID */
#element-id

/* Class */
.class-name

/* 属性 */
[attribute]
[attribute="value"]
[attribute*="contains"]
[attribute^="starts-with"]
[attribute$="ends-with"]
```

**组合器:**
```css
/* 后代 */
div p                  /* div内的任何p */

/* 子元素 */
div > p                /* div的直接子p */

/* 相邻兄弟 */
h1 + p                 /* h1后的第一个p */

/* 通用兄弟 */
h1 ~ p                 /* h1后的所有p */
```

**伪类:**
```css
/* 状态 */
:hover, :focus, :active, :visited

/* 位置 */
:first-child, :last-child
:nth-child(n), :nth-of-type(n)

/* 内容 */
:empty, :not(selector)
```

**Playwright特殊选择器:**
```css
/* 文本内容 */
button:has-text("Submit")
:text("exact text")

/* 可见性 */
:visible

/* 布局 */
:above(:text("Label"))
:below(:text("Header"))
:left-of(:text("Button"))
:right-of(:text("Text"))
```

### B. 等待策略比较

| 策略 | 等待条件 | 使用场景 | 速度 |
|------|----------|----------|------|
| `load` | 完整页面加载(包括资源) | 完整渲染,重图像页面 | 慢 |
| `domcontentloaded` | DOM就绪(不等资源) | 快速交互,SPA | 快 |
| `networkidle` | 无网络活动500ms | AJAX密集型,动态内容 | 最慢 |
| `commit` | 导航提交 | 快速导航检测 | 最快 |

**推荐:**
- **一般使用:** `load`
- **快速抓取:** `domcontentloaded`
- **动态内容:** `networkidle`

### C. 常见错误代码

| 错误 | 含义 | 解决方案 |
|------|------|----------|
| `Timeout` | 操作超时 | 增加超时或检查选择器 |
| `TargetClosedError` | 页面/浏览器已关闭 | 检查会话管理 |
| `NavigationError` | 导航失败 | 检查URL和网络 |
| `ElementNotFound` | 元素未找到 | 验证选择器,添加等待 |
| `InvalidSelector` | 选择器无效 | 修复选择器语法 |

### D. 性能优化清单

- [ ] 使用 `headless: true`
- [ ] 设置适当的等待策略
- [ ] 禁用不需要的资源(图片、CSS)
- [ ] 重用会话进行多个操作
- [ ] 设置合理的超时
- [ ] 限制并发会话
- [ ] 启用会话超时自动清理
- [ ] 使用选择性截图
- [ ] 避免不必要的整页截图
- [ ] 监控资源使用

### E. 安全清单

- [ ] 启用URL验证
- [ ] 配置适当的黑名单
- [ ] 阻止本地网络(除非需要)
- [ ] 对敏感操作启用批准
- [ ] 验证表单数据
- [ ] 使用HTTPS URL
- [ ] 不在配置中硬编码凭据
- [ ] 定期审查会话
- [ ] 监控异常活动
- [ ] 保持Playwright更新

---

**状态:** ✅ 生产就绪
**文档版本:** 1.0
**最后更新:** 2026-01-31
**作者:** Claude Code (Anthropic)
