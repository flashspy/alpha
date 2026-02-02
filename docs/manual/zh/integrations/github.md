# GitHub 集成用户指南

**Alpha v1.2 - Phase 11.2 功能**

---

## 概述

GitHub集成功能使Alpha能够通过自然语言命令或显式工具调用直接与GitHub仓库、issues、pull requests和commits进行交互。此集成消除了上下文切换,让您可以直接从Alpha的命令行管理GitHub工作流程。

---

## 功能特性

✅ **仓库管理**
- 使用过滤器列出您的仓库
- 获取详细的仓库信息
- 查看仓库元数据(stars、forks、语言)

✅ **Issue跟踪**
- 使用状态和标签过滤器列出issues
- 查看详细的issue信息
- 创建新issues
- 向现有issues添加评论

✅ **Pull Request管理**
- 按状态列出pull requests
- 查看PR详情和合并状态
- 检查PR可合并性和CI状态
- **创建新的pull requests** ✨ 新功能
- 支持draft（草稿）PR

✅ **提交历史**
- 浏览提交历史
- 查看详细的commit信息
- 跨分支跟踪更改

✅ **智能功能**
- 自动速率限制处理
- 响应缓存以提高性能
- 失败请求的重试逻辑
- 自然语言命令支持

---

## 设置

### 1. 获取GitHub个人访问令牌

1. 访问 https://github.com/settings/tokens
2. 点击"Generate new token" → "Generate new token (classic)"
3. 给它一个描述性名称:"Alpha GitHub Integration"
4. 选择权限范围:
   - `repo` (私有仓库的完全控制)
   - `read:org` (可选,用于组织访问)
5. 点击"Generate token"
6. **立即复制令牌**(之后无法再次查看!)

### 2. 配置环境变量

将您的令牌添加到环境中:

```bash
# Linux/macOS - 添加到 ~/.bashrc 或 ~/.zshrc
export GITHUB_TOKEN="your_token_here"

# 或为当前会话临时设置
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

### 3. 验证设置

启动Alpha并验证GitHub工具可用:

```bash
alpha> tools

可用工具:
- github: 与GitHub仓库、issues、PRs和commits交互
- ...
```

---

## 使用方法

### 仓库操作

#### 列出您的仓库

```bash
# 列出所有您的仓库
alpha> 显示我的GitHub仓库

# 列出特定用户的仓库
alpha> 列出torvalds的仓库

# 使用显式工具调用
alpha> github list_repos
```

#### 获取仓库信息

```bash
# 自然语言
alpha> 告诉我关于torvalds/linux仓库的信息

# 显式调用
alpha> github get_repo owner=torvalds repo=linux
```

**输出包括:**
- 仓库名称和描述
- Stars、forks、watchers数量
- 主要语言
- 开放issues数量
- 克隆URLs(HTTPS和SSH)
- 创建和更新时间戳

---

### Issue管理

#### 列出Issues

```bash
# 列出开放的issues
alpha> 显示facebook/react中的开放issues

# 列出所有issues(开放和关闭)
alpha> 列出microsoft/vscode的所有issues

# 按标签过滤
alpha> github list_issues owner=facebook repo=react labels=bug,help-wanted state=open
```

#### 查看Issue详情

```bash
# 自然语言
alpha> 显示facebook/react的issue #123

# 显式调用
alpha> github get_issue owner=facebook repo=react number=123
```

**输出包括:**
- Issue标题和内容
- 作者和受理人
- 标签和里程碑
- 评论数量
- 创建和更新时间戳
- 当前状态(开放/关闭)

#### 创建新Issue

```bash
# 使用自然语言
alpha> 在myuser/myrepo中创建一个issue,标题是"Bug: 登录失败",描述是"更新后用户无法登录"

# 显式调用
alpha> github create_issue owner=myuser repo=myrepo title="Bug: 登录失败" body="更新后用户无法登录" labels=bug,high-priority
```

#### 向Issue添加评论

```bash
# 自然语言
alpha> 向myuser/myrepo的issue #5添加评论:"正在修复中"

# 显式调用
alpha> github add_comment owner=myuser repo=myrepo number=5 body="正在修复中"
```

---

### Pull Request管理

#### 列出Pull Requests

```bash
# 列出开放的PRs
alpha> 显示microsoft/vscode的开放pull requests

# 列出所有PRs
alpha> github list_prs owner=facebook repo=react state=all

# 按最近更新排序
alpha> github list_prs owner=django repo=django sort=updated direction=desc
```

#### 查看Pull Request详情

```bash
# 自然语言
alpha> 告诉我facebook/react的PR #456

# 显式调用
alpha> github get_pr owner=facebook repo=react number=456
```

**输出包括:**
- PR标题、内容和作者
- 源分支和目标分支
- 合并状态(可合并、冲突、检查)
- 草稿/就绪状态
- Commits、additions、deletions
- 更改的文件数量
- 标签和受理人

#### 创建Pull Request ✨ 新功能

```bash
# 使用自然语言
alpha> 在myuser/myrepo中从feature-branch到main创建PR,标题为"添加新功能"

# 使用完整选项的显式调用
alpha> github create_pr owner=myuser repo=myrepo title="添加新功能" head=feature-branch base=main body="此PR实现了issue #42中讨论的新功能"

# 创建草稿PR
alpha> github create_pr owner=myuser repo=myrepo title="WIP: 进行中的工作" head=wip-feature base=develop draft=true body="仍在编写测试"
```

**参数:**
- `owner` (必需): 仓库所有者用户名
- `repo` (必需): 仓库名称
- `title` (必需): Pull request标题
- `head` (必需): 源分支(您的更改所在位置)
- `base` (必需): 目标分支(您想要合并到的位置)
- `body` (可选): PR描述
- `draft` (可选): 创建为草稿PR (默认: false)
- `maintainer_can_modify` (可选): 允许维护者编辑 (默认: true)

**输出:**
- PR编号
- PR标题和URL
- 源分支和目标分支名称
- 草稿状态
- 当前状态(open)

---

### Commit操作

#### 列出Commits

```bash
# 列出最近的commits
alpha> 显示torvalds/linux的最近commits

# 列出特定分支的commits
alpha> github list_commits owner=myuser repo=myrepo sha=develop

# 限制页数
alpha> github list_commits owner=facebook repo=react max_pages=2
```

#### 查看Commit详情

```bash
# 自然语言
alpha> 显示torvalds/linux的commit abc123

# 显式调用
alpha> github get_commit owner=torvalds repo=linux sha=abc123def456
```

**输出包括:**
- 完整commit SHA
- Commit消息
- 作者和提交者信息
- 时间戳
- 父commits
- GitHub URL

---

### 实用工具操作

#### 检查速率限制

```bash
alpha> github rate_limit
```

**输出:**
- API调用限制(通常5000/小时)
- 剩余调用次数
- 重置时间(Unix时间戳)
- 已使用的调用次数

---

## 高级用法

### 自动化示例

#### 监控Issue活动

```bash
# 创建每日检查新issues的计划任务
alpha> 安排每天上午9点运行的任务:"列出myuser/myrepo中的开放issues,如果超过10个则通知我"
```

#### 自动PR审查提醒

```bash
# 获取需要审查的PRs通知
alpha> 检查myuser/myrepo中的开放PRs,如果有任何等待超过2天的则提醒我
```

---

## API速率限制

GitHub API有速率限制:

- **认证请求**: 5,000请求/小时
- **搜索API**: 30请求/分钟

Alpha自动处理速率限制:

- **缓冲保留**: 保留100个API调用
- **自动重试**: 使用退避策略重试失败的请求
- **缓存**: 缓存响应5分钟以减少API调用
- **速率限制错误**: 显示清晰的错误消息和重置时间

**检查剩余配额:**
```bash
alpha> github rate_limit
```

---

## 故障排除

### "Authentication failed"错误

**原因**: 无效或缺失的GitHub令牌

**解决方案**:
1. 验证`GITHUB_TOKEN`已设置: `echo $GITHUB_TOKEN`
2. 检查令牌是否过期
3. 如需要,生成新令牌
4. 设置令牌后重启Alpha

### "Resource not found"错误

**原因**: 仓库、issue或PR不存在或您无权访问

**解决方案**:
1. 检查owner/repo名称拼写
2. 验证issue/PR编号正确
3. 确保您有权访问私有仓库(令牌范围)

### "Rate limit exceeded"错误

**原因**: 短时间内API请求过多

**解决方案**:
1. 等待速率限制重置(错误消息中显示)
2. 使用缓存(默认启用)
3. 降低请求频率
4. 检查速率限制状态: `alpha> github rate_limit`

### "Insufficient permissions"错误

**原因**: 令牌没有所需的权限范围

**解决方案**:
1. 前往GitHub上的令牌设置
2. 添加所需范围(私有仓库需要`repo`)
3. 重新生成令牌
4. 更新`GITHUB_TOKEN`环境变量

---

## 安全最佳实践

✅ **令牌存储**
- 将令牌存储在环境变量中,永远不要存在代码中
- 使用`~/.bashrc`或`~/.zshrc`进行持久存储
- 永远不要将令牌提交到版本控制

✅ **令牌权限**
- 授予最小所需权限范围
- 使用细粒度令牌以获得更好的安全性
- 定期轮换令牌

✅ **访问控制**
- 保持令牌私密和安全
- 如果泄露立即撤销令牌
- 定期在GitHub上审查令牌使用情况

---

## 示例和用例

### 开发者工作流程

```bash
# 早上例行:检查您的仓库
alpha> 列出我的仓库,按最近更新排序

# 检查开放issues
alpha> 显示myuser/myproject中的开放issues

# 审查需要关注的PRs
alpha> 列出myuser/myproject的开放pull requests

# 为发现的bug创建issue
alpha> 在myuser/myproject中创建issue:"登录表单bug" body="邮箱验证不工作"
```

### 开源贡献

```bash
# 查找有趣的项目
alpha> 获取facebook/react的仓库信息

# 查看可贡献的开放issues
alpha> 列出facebook/react的issues,标签为good-first-issue,状态为开放

# 查看特定issue详情
alpha> 显示facebook/react的issue #12345
```

### 项目管理

```bash
# 每日站会:审查团队活动
alpha> 列出myorg/project的commits

# 检查sprint进度
alpha> 列出myorg/project的issues,里程碑为v2.0,状态为开放

# 监控PR审查队列
alpha> 列出myorg/project的PRs,状态为开放,按创建时间升序排序
```

---

## 限制

⚠️ **当前限制**(Phase 11.2):
- 无PR合并(仅查看和创建)
- 无issue编辑(仅创建和评论)
- 无分支操作
- 无webhooks或实时通知
- 无GitHub Actions集成

**未来阶段计划**:
- 完整PR管理(合并、审查、批准)
- Issue编辑和关闭
- 分支管理
- Webhook支持实时更新
- GitHub Actions集成

---

## 常见问题

**问: 我需要付费的GitHub账户吗?**
答: 不需要,免费的GitHub账户提供5,000 API请求/小时,对大多数用例来说已经足够。

**问: 我可以在GitHub Enterprise中使用吗?**
答: 可以,创建客户端时设置`base_url`参数: `GitHubClient(base_url="https://github.company.com/api/v3")`

**问: 我的数据是私密的吗?**
答: 是的,所有GitHub操作都使用您的个人令牌。Alpha不会存储或共享您的GitHub数据。

**问: 我可以从错误自动创建issues吗?**
答: 可以!Alpha的主动智能可以在检测到错误或失败时建议创建issues。

**问: 如何访问私有仓库?**
答: 确保您的令牌具有`repo`权限范围,该范围授予对私有仓库的访问权限。

---

## 相关文档

- [Alpha功能指南](../features.md)
- [工具使用指南](../../TOOL_USAGE_GUIDE.md)
- [任务调度](../daemon_mode.md)
- [GitHub API文档](https://docs.github.com/en/rest)

---

**版本**: 1.2 (Phase 11.2)
**最后更新**: 2026-02-03
**状态**: 生产就绪 ✅
