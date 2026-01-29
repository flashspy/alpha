# 已安装的 Agent Skills

## 安装日期
2026-01-29

## 安装方法
使用 `npx skills add <owner/repo>` 命令从 skills.sh 市场安装

## 技能来源
- Skills.sh: https://skills.sh/
- 配置文件: `config.yaml`

## 已安装技能列表 (共20个)

### 1. vercel-react-best-practices
- **来源**: vercel-labs/agent-skills
- **安装量**: 67,481
- **描述**: React和Next.js性能优化指南
- **用途**: 编写、审查或重构React/Next.js代码时使用

### 2. web-design-guidelines
- **来源**: vercel-labs/agent-skills
- **安装量**: 52,273
- **描述**: Web界面设计指南
- **用途**: 检查UI合规性、可访问性、设计审查

### 3. vercel-composition-patterns
- **来源**: vercel-labs/agent-skills
- **安装量**: 7,623
- **描述**: React组件组合模式
- **用途**: 重构组件、构建可扩展的组件库

### 4. vercel-react-native-skills
- **来源**: vercel-labs/agent-skills
- **安装量**: 5,963
- **描述**: React Native和Expo最佳实践
- **用途**: 构建高性能移动应用

### 5. remotion-best-practices
- **来源**: remotion-dev/skills
- **安装量**: 47,747
- **描述**: Remotion视频制作最佳实践
- **用途**: 使用React创建程序化视频

### 6. find-skills
- **来源**: vercel-labs/skills
- **安装量**: 39,936
- **描述**: 查找和发现技能
- **用途**: 搜索可用的技能

### 7. frontend-design
- **来源**: anthropics/skills
- **安装量**: 26,209
- **描述**: 前端设计指南
- **用途**: 前端开发设计决策

### 8. skill-creator
- **来源**: anthropics/skills
- **安装量**: 14,723
- **描述**: 创建新技能的辅助工具
- **用途**: 开发自定义技能

### 9. agent-browser
- **来源**: vercel-labs/agent-browser
- **安装量**: 13,651
- **描述**: Agent浏览器工具
- **用途**: Agent的浏览器操作能力

### 10. supabase-postgres-best-practices
- **来源**: supabase/agent-skills
- **安装量**: 6,963
- **描述**: Supabase和PostgreSQL最佳实践
- **用途**: 数据库设计和查询优化

### 11. seo-audit
- **来源**: coreyhaines31/marketingskills
- **安装量**: 7,404
- **描述**: SEO审核工具
- **用途**: 网站SEO分析和优化建议

### 12. audit-website
- **来源**: squirrelscan/skills
- **安装量**: 7,157
- **描述**: 网站审核工具
- **用途**: 全面的网站质量审核

### 13. ui-ux-pro-max
- **来源**: nextlevelbuilder/ui-ux-pro-max-skill
- **安装量**: 6,666
- **描述**: UI/UX专业技能
- **用途**: 高级UI/UX设计指导

### 14. copywriting
- **来源**: coreyhaines31/marketingskills
- **安装量**: 5,596
- **描述**: 文案写作技能
- **用途**: 营销文案创作

### 15. pdf
- **来源**: anthropics/skills
- **安装量**: 5,246
- **描述**: PDF文档处理
- **用途**: 创建和操作PDF文件

### 16. better-auth-best-practices
- **来源**: better-auth/skills
- **安装量**: 5,145
- **描述**: Better Auth最佳实践
- **用途**: 身份验证和授权实现

### 17. brainstorming
- **来源**: obra/superpowers
- **安装量**: 4,852
- **描述**: 头脑风暴辅助工具
- **用途**: 创意生成和问题解决

### 18. docx
- **来源**: anthropics/skills
- **描述**: Word文档处理
- **用途**: 创建和编辑DOCX文件

### 19. pptx
- **来源**: anthropics/skills
- **描述**: PowerPoint文档处理
- **用途**: 创建和编辑PPTX文件

### 20. xlsx
- **来源**: anthropics/skills
- **描述**: Excel文档处理
- **用途**: 创建和编辑XLSX文件

## 安装位置
`.agents/skills/` - 项目级技能目录

## 管理命令

### 查看已安装技能
```bash
npx skills list
```

### 搜索技能
```bash
npx skills find
```

### 添加技能
```bash
npx skills add <owner/repo>
npx skills add <owner/repo> --skill <skill-name>
```

### 删除技能
```bash
npx skills remove <skill-name>
```

### 更新技能
```bash
npx skills update
```

## 技能分类

### 前端开发 (8个)
- vercel-react-best-practices
- web-design-guidelines
- vercel-composition-patterns
- vercel-react-native-skills
- frontend-design
- ui-ux-pro-max
- remotion-best-practices
- agent-browser

### 文档处理 (3个)
- pdf
- docx
- pptx
- xlsx

### 营销与内容 (2个)
- seo-audit
- copywriting

### 数据库与认证 (2个)
- supabase-postgres-best-practices
- better-auth-best-practices

### 审核与分析 (1个)
- audit-website

### 工具与辅助 (4个)
- find-skills
- skill-creator
- brainstorming

## 注意事项
1. 技能通过符号链接安装到 `.agents/skills/` 目录
2. 技能使用 SKILL.md 格式（YAML frontmatter + Markdown指令）
3. 所有技能都与 Claude Code Agent 兼容
4. 技能会被自动检测和加载

## 下一步
- 测试关键技能确保正常工作
- 根据需要调整 Alpha 系统以支持 SKILL.md 格式
- 考虑实现技能的自动加载和执行机制
