# Alpha 自动技能系统 - 快速使用指南

## 🚀 立即体验

### 1. 启动 Alpha

```bash
# 进入项目目录
cd /home/zhang/bot/alpha

# 启动 Alpha（会自动启用自动技能系统）
./start.sh
```

**启动时你会看到**:
```
Loading builtin skills...
✓ Loaded 4 builtin skills

Connecting to skill sources...
Found 1 skill sources

Initializing auto-skill system...
✓ Auto-skill system ready

Alpha AI Assistant
Type 'help' for commands, 'quit' to exit
```

### 2. 开始对话 - 自动技能会自动激活

#### 示例 1: React 开发

```
You: Help me create a high-performance React component

系统响应:
Analyzing query for relevant skills...
🎯 Using skill: vercel-react-best-practices (relevance: 7.0/10)
Thinking...

Alpha: [根据 Vercel 的 React 最佳实践指南响应]
```

#### 示例 2: PDF 文档

```
You: Create a PDF invoice template

系统响应:
Analyzing query for relevant skills...
🎯 Using skill: pdf (relevance: 15.5/10)
Thinking...

Alpha: [使用 PDF 技能的专业指导创建发票模板]
```

#### 示例 3: UI 设计

```
You: Design a beautiful login page

系统响应:
Analyzing query for relevant skills...
🎯 Using skill: web-design-guidelines (relevance: 7.0/10)
Thinking...

Alpha: [按照 Web 设计指南提供设计建议]
```

#### 示例 4: SEO 优化

```
You: Audit my website for SEO issues

系统响应:
Analyzing query for relevant skills...
🎯 Using skill: seo-audit (relevance: 5.5/10)
Thinking...

Alpha: [提供全面的 SEO 审核清单和建议]
```

#### 示例 5: 数据库优化

```
You: Optimize my PostgreSQL queries

系统响应:
Analyzing query for relevant skills...
🎯 Using skill: supabase-postgres-best-practices (relevance: 6.0/10)
Thinking...

Alpha: [根据 Supabase 的 PostgreSQL 最佳实践提供优化建议]
```

### 3. 工作原理

```
用户输入
    ↓
自动分析关键词
    ↓
匹配最相关的技能
    ↓
检查是否已安装 (如未安装则自动下载)
    ↓
加载技能指令为上下文
    ↓
LLM 按技能指令响应
```

### 4. 当前已安装的技能（20个）

**前端开发**:
- vercel-react-best-practices
- web-design-guidelines
- frontend-design
- vercel-composition-patterns
- vercel-react-native-skills
- ui-ux-pro-max
- remotion-best-practices
- agent-browser

**文档处理**:
- pdf
- docx
- pptx
- xlsx

**营销与内容**:
- seo-audit
- copywriting

**数据库与认证**:
- supabase-postgres-best-practices
- better-auth-best-practices

**工具与辅助**:
- find-skills
- skill-creator
- brainstorming
- audit-website

### 5. 什么时候会触发自动技能？

自动技能系统会分析你的输入，当检测到以下关键词或主题时自动激活：

- **React/前端**: react, component, next.js, frontend, ui, design
- **文档**: pdf, word, excel, powerpoint, document
- **SEO/营销**: seo, optimization, copywriting, marketing
- **数据库**: database, postgres, sql, query
- **认证**: auth, authentication, login, user
- **移动应用**: mobile, react native, ios, android
- **视频**: video, animation, remotion
- **审核**: audit, review, analyze

**相关性评分**:
- 10分: 完全匹配（如输入"pdf"时匹配"pdf"技能）
- 5-7分: 关键词匹配
- 3分: 阈值（低于3分不会自动加载）

### 6. 如何验证技能是否在使用？

#### 方法 1: 观察输出
当技能被自动加载时，你会看到：
```
🎯 Using skill: [技能名称] (relevance: [分数]/10)
```

#### 方法 2: 检查响应质量
使用技能的响应会：
- 更专业和深入
- 遵循特定领域的最佳实践
- 包含更详细的指导

#### 方法 3: 查看日志
```bash
# 启动时加入调试模式
DEBUG=1 ./start.sh

# 查看日志
tail -f logs/alpha.log | grep "Auto-loaded skill"
```

### 7. 配置选项

编辑 `config.yaml`:

```yaml
skills:
  auto_skill:
    enabled: true           # 启用/禁用自动技能
    auto_install: true      # 自动安装缺失的技能
    auto_load: true         # 自动加载技能上下文
    min_score: 3.0          # 最低相关性分数（0-10）
    max_matches: 3          # 每次查询最多考虑的技能数
```

**调整建议**:
- **更激进**: `min_score: 2.0` - 更容易触发技能
- **更保守**: `min_score: 5.0` - 只在高度相关时使用
- **禁用**: `enabled: false` - 完全关闭自动技能

### 8. 手动管理技能

#### 查看已安装技能
```
You: skills
```

#### 搜索技能
```
You: search skill react
```

#### 查看技能使用统计
```python
# Python API
manager.get_usage_stats()
# 返回: {'vercel-react-best-practices': 5, 'pdf': 3, ...}
```

### 9. 常见问题

#### Q: 技能没有自动加载？
A: 可能原因：
1. 相关性分数低于阈值（默认3.0）
2. 没有匹配的技能
3. 自动技能被禁用

**解决方法**:
```yaml
# 降低阈值
min_score: 2.0
```

#### Q: 如何知道哪些技能可用？
A:
```bash
# 查看已安装
npx skills list

# 浏览市场
open https://skills.sh/
```

#### Q: 可以同时使用多个技能吗？
A: 当前版本每次只使用一个最相关的技能。多技能组合在路线图中。

#### Q: 技能会影响性能吗？
A: 影响很小：
- 首次匹配: ~200ms（加载缓存）
- 后续匹配: <10ms
- 技能加载: <20ms

### 10. 测试示例对话

#### 完整对话流程示例

```bash
$ ./start.sh

Loading builtin skills...
✓ Loaded 4 builtin skills
Initializing auto-skill system...
✓ Auto-skill system ready

Alpha AI Assistant
-------------------

You: I need to create a React component for displaying user profiles

Analyzing query for relevant skills...
🎯 Using skill: vercel-react-best-practices (relevance: 7.0/10)
Thinking...

Alpha: I'll help you create a performant React component for user profiles
following Vercel's best practices:

1. Component Structure:
```tsx
interface UserProfile {
  id: string;
  name: string;
  avatar: string;
  bio: string;
}

export function UserProfileCard({ profile }: { profile: UserProfile }) {
  return (
    <div className="profile-card">
      <img src={profile.avatar} alt={profile.name} />
      <h2>{profile.name}</h2>
      <p>{profile.bio}</p>
    </div>
  );
}
```

2. Performance Optimizations:
- Use React.memo for expensive renders
- Lazy load images
- Optimize re-renders

[... 详细的最佳实践建议 ...]

---

You: Now create a PDF export feature for this

Analyzing query for relevant skills...
🎯 Using skill: pdf (relevance: 15.5/10)
Thinking...

Alpha: I'll help you add PDF export functionality:

[... PDF 创建的专业指导 ...]
```

### 11. 进阶使用

#### Python API 集成

```python
from alpha.skills import AutoSkillManager

# 初始化
manager = AutoSkillManager()
await manager.initialize()

# 获取技能建议（不自动安装）
suggestions = await manager.suggest_skills("build a React app", max_suggestions=5)

for skill in suggestions:
    print(f"{skill['name']}: {skill['score']:.1f} ({skill['installs']:,} installs)")

# 手动加载特定技能
context = await manager.get_skill_context("vercel-react-best-practices")
```

### 12. 下一步

1. **体验各种场景**: 尝试不同类型的请求，观察技能匹配
2. **调整配置**: 根据使用体验调整 `min_score`
3. **探索技能**: 浏览 https://skills.sh/ 了解更多技能
4. **查看文档**: 阅读 `docs/AUTO_SKILL_SYSTEM.md` 了解详细信息

## 🎉 开始使用

现在就启动 Alpha，体验自动技能系统的强大功能！

```bash
./start.sh
```

然后随便聊一个与前端、PDF、SEO、数据库相关的话题，看看系统如何自动选择和使用相关技能！
