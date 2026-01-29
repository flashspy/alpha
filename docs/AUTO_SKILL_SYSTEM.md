# Alpha 自动技能系统 (Auto-Skill System)

## 概述

Alpha 的自动技能系统能够智能地发现、下载、安装并执行相关的 Agent Skills，无需用户手动干预。

## 核心功能

### 1. 智能技能匹配 (Skill Matching)
- 分析用户请求，识别关键词和意图
- 从 skills.sh 市场搜索相关技能
- 按相关性和流行度排序
- 自动选择最佳匹配技能

### 2. 自动下载安装 (Auto-Installation)
- 检测技能是否已安装
- 使用 `npx skills` 自动安装缺失的技能
- 处理安装错误和超时
- 追踪已安装技能

### 3. 动态加载执行 (Dynamic Loading)
- 读取 SKILL.md 文件内容
- 解析 YAML frontmatter 和 Markdown 指令
- 将技能指令加载为 LLM 上下文
- LLM 根据技能指令响应用户

## 系统架构

```
用户请求
    ↓
SkillMatcher (分析并匹配技能)
    ↓
SkillDownloader (自动安装)
    ↓
SkillLoader (加载 SKILL.md)
    ↓
AutoSkillManager (协调管理)
    ↓
LLM (使用技能指令响应)
```

## 核心组件

### 1. SkillMatcher
**文件**: `alpha/skills/matcher.py`

**功能**:
- 从 skills.sh API 加载技能列表
- 关键词提取和相关性计算
- 按分数和安装量排序

**示例**:
```python
from alpha.skills import SkillMatcher

matcher = SkillMatcher()
await matcher.load_skills_cache()

matches = matcher.match_skills("Help me build a React component", max_results=3)
# 返回: [
#   {name: 'vercel-react-best-practices', score: 7.0, installs: 67544},
#   {name: 'frontend-design', score: 6.0, installs: 26237},
#   ...
# ]
```

### 2. SkillDownloader
**文件**: `alpha/skills/downloader.py`

**功能**:
- 检查技能是否已安装
- 使用 npx skills 自动安装
- 错误处理和重试机制

**示例**:
```python
from alpha.skills import SkillDownloader

downloader = SkillDownloader()

# 检查是否已安装
if not downloader.is_installed("vercel-react-best-practices"):
    # 自动安装
    result = await downloader.install_skill_by_id(
        "vercel-react-best-practices",
        "vercel-labs/agent-skills"
    )
```

### 3. SkillLoader
**文件**: `alpha/skills/loader.py`

**功能**:
- 加载 SKILL.md 文件
- 解析 YAML frontmatter
- 格式化为 LLM 上下文

**示例**:
```python
from alpha.skills import SkillLoader

loader = SkillLoader()

# 加载技能上下文
context = loader.get_skill_context("vercel-react-best-practices")
# 返回格式化的指令文本，供 LLM 使用
```

### 4. AutoSkillManager
**文件**: `alpha/skills/auto_manager.py`

**功能**:
- 协调上述所有组件
- 端到端自动化工作流
- 技能使用统计

**示例**:
```python
from alpha.skills import AutoSkillManager

manager = AutoSkillManager(auto_install=True, auto_load=True)
await manager.initialize()

# 处理用户查询
result = await manager.process_query("Help me create a React component")

if result:
    skill_name = result['skill_name']
    skill_context = result['context']
    # 将 context 加入 LLM 提示
```

## 配置说明

**配置文件**: `config.yaml`

```yaml
skills:
  # Automatic Skill Discovery and Execution
  auto_skill:
    # 启用自动技能发现
    enabled: true
    # 自动安装缺失的技能
    auto_install: true
    # 自动加载技能上下文
    auto_load: true
    # 最低相关性分数 (0-10)
    min_score: 3.0
    # 每次查询考虑的最大技能数
    max_matches: 3

  # 技能源配置
  sources:
    - name: "Skills.sh"
      url: "https://skills.sh/api/skills"
      type: "api"
      enabled: true
      priority: 1

  # 下载的技能目录
  downloaded_dir: ".agent/skills"
```

## 工作流程

### 自动技能执行流程

1. **用户输入**: "Help me create a beautiful React component"

2. **技能匹配** (SkillMatcher):
   ```
   - 提取关键词: ['react', 'component', 'design']
   - 搜索 skills.sh API
   - 匹配结果:
     * vercel-react-best-practices (score: 7.0)
     * frontend-design (score: 6.0)
     * web-design-guidelines (score: 7.0)
   - 选择最佳: vercel-react-best-practices
   ```

3. **自动安装** (SkillDownloader):
   ```
   - 检查是否已安装: ✓ 已安装
   - 跳过安装步骤
   ```

4. **加载技能** (SkillLoader):
   ```
   - 读取: .agents/skills/vercel-react-best-practices/SKILL.md
   - 解析 frontmatter 和指令
   - 格式化为上下文
   ```

5. **LLM 响应**:
   ```
   - 接收用户请求 + 技能上下文
   - 按照技能指令生成响应
   - 应用 React 最佳实践
   ```

## 使用示例

### 示例 1: React 组件开发

**用户**: "Help me build a performant React component"

**系统流程**:
1. 匹配技能: `vercel-react-best-practices` (67K installs)
2. 已安装 ✓
3. 加载上下文
4. LLM 响应包含:
   - React 性能优化指南
   - 组件设计最佳实践
   - Next.js 特定建议

### 示例 2: PDF 文档生成

**用户**: "Create a PDF invoice for my customer"

**系统流程**:
1. 匹配技能: `pdf` (5.2K installs)
2. 已安装 ✓
3. 加载 PDF 操作指令
4. LLM 响应包含:
   - PDF 创建步骤
   - 发票模板建议
   - 格式化指导

### 示例 3: SEO 优化

**用户**: "Audit my website for SEO issues"

**系统流程**:
1. 匹配技能: `seo-audit` (7.4K installs)
2. 已安装 ✓
3. 加载 SEO 审核指令
4. LLM 响应包含:
   - SEO 审核清单
   - 常见问题检查
   - 优化建议

## API 参考

### AutoSkillManager

#### 初始化
```python
manager = AutoSkillManager(
    skills_dir=Path(".agents/skills"),  # 技能目录
    auto_install=True,                  # 自动安装
    auto_load=True                      # 自动加载
)
await manager.initialize()              # 加载技能缓存
```

#### 处理查询
```python
result = await manager.process_query(query)
# 返回:
# {
#     'skill_name': str,      # 技能名称
#     'skill_source': str,    # 来源仓库
#     'context': str,         # 技能上下文
#     'score': float,         # 相关性分数
#     'installs': int,        # 安装量
#     'matches': List[Dict]   # 所有匹配项
# }
```

#### 获取技能上下文
```python
context = await manager.get_skill_context("skill-name")
# 返回格式化的技能指令文本
```

#### 建议技能
```python
suggestions = await manager.suggest_skills(query, max_suggestions=5)
# 返回技能列表（不自动安装）
```

#### 列出已安装技能
```python
installed = manager.list_installed_skills()
# 返回: [{'name': str, 'description': str}, ...]
```

#### 使用统计
```python
stats = manager.get_usage_stats()
# 返回: {'skill-name': count, ...}
```

## 技能相关性评分

评分系统 (0-10分):

- **完全匹配** (+10): 查询包含技能名称
- **关键词匹配** (+5): 技能名称包含关键词
- **流行度加成**:
  - >50K 安装 (+2)
  - >20K 安装 (+1)
  - >5K 安装 (+0.5)

**示例**:
```
查询: "Create a PDF document"
技能: "pdf"
评分: 15.5分
  - 完全匹配: +10
  - 关键词'pdf': +5
  - 5.2K 安装: +0.5
```

## 测试

**运行测试**:
```bash
python tests/test_auto_skill.py
```

**测试覆盖**:
1. ✅ 技能匹配测试
2. ✅ 自动安装测试
3. ✅ 技能加载测试
4. ✅ 端到端工作流测试

## 优势

### 1. 零配置
- 无需手动安装技能
- 自动发现相关技能
- 智能匹配最佳选项

### 2. 动态扩展
- 随时添加新技能
- 无需重启系统
- 即时生效

### 3. 上下文感知
- 根据用户请求加载相关指令
- LLM 获得特定领域知识
- 提供更专业的响应

### 4. 性能优化
- 技能缓存机制
- 只在需要时安装
- 轻量级集成

## 注意事项

1. **网络依赖**: 首次使用需要网络连接下载技能
2. **磁盘空间**: 技能文件保存在 `.agents/skills/` 目录
3. **Node.js 要求**: 使用 `npx skills` 需要 Node.js 环境
4. **相关性阈值**: 可调整 `min_score` 以控制触发条件

## 故障排除

### 问题 1: 技能匹配失败
**症状**: 没有找到相关技能

**解决**:
```bash
# 检查网络连接
curl -s https://skills.sh/api/skills

# 手动初始化缓存
python -c "
from alpha.skills import SkillMatcher
import asyncio
matcher = SkillMatcher()
asyncio.run(matcher.load_skills_cache())
"
```

### 问题 2: 安装失败
**症状**: npx skills 命令出错

**解决**:
```bash
# 检查 Node.js 和 npx
node --version
npx --version

# 手动安装测试
npx skills add vercel-labs/agent-skills --skill find-skills --yes
```

### 问题 3: 技能未加载
**症状**: context 为 None

**解决**:
```bash
# 检查技能文件是否存在
ls -la .agents/skills/

# 验证 SKILL.md 文件
cat .agents/skills/find-skills/SKILL.md
```

## 路线图

### 已完成 ✅
- [x] 智能技能匹配
- [x] 自动下载安装
- [x] 动态加载执行
- [x] 使用统计追踪
- [x] 完整测试覆盖

### 计划中 🚧
- [ ] 技能推荐系统
- [ ] 学习用户偏好
- [ ] 多技能组合
- [ ] 技能版本管理
- [ ] 离线技能缓存

## 相关文档

- [已安装技能列表](./INSTALLED_SKILLS.md)
- [Skills.sh 市场](https://skills.sh/)
- [技能开发指南](https://skills.sh/docs)
- [配置文件](../config.yaml)

## 贡献

欢迎贡献新功能和改进！

**开发者**: Alpha 开发团队
**版本**: v0.5.0
**日期**: 2026-01-29
**状态**: ✅ 生产就绪
