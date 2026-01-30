# 文档整理说明

## 整理日期
2026-01-29

## 整理原则

1. **用户文档** - 最终用户需要的，放在 `docs/` 目录
2. **内部文档** - 开发团队需要的，放在 `docs/internal/` 目录
3. **过程文档** - 开发过程产生的，归档到 `archive/` 目录

## 文档结构

### 用户文档 (docs/)

```
docs/
├── index.md                    # 文档索引
├── zh/                         # 中文文档
│   ├── quickstart.md          # 快速开始
│   ├── features.md            # 功能详解
│   └── anthropic_config.md    # 配置指南
└── en/                         # 英文文档
    ├── quickstart.md
    ├── features.md
    └── anthropic_config.md
```

### 内部文档 (docs/internal/)

```
docs/internal/
├── requirements.md            # 需求文档
├── architecture.md            # 架构设计
├── phase1_report.md          # Phase 1 开发报告
├── project_summary.md        # 项目总结
└── development_plan.md       # 开发计划
```

### 根目录文档

```
./
├── README.md                  # 中文README
├── README.en.md              # 英文README
├── HOW_TO_RUN.md             # 运行指南
└── CHANGELOG.md              # 变更日志
```

### 归档文档 (archive/)

已归档的过程文档：
- alpha.md - 原始需求文档
- PROJECT_COMPLETE.md - Phase 1 完成报告
- RELEASE_NOTES.md - v0.1.0 发布说明
- NEXT_STEPS.md - 下一步计划（已整合到 development_plan.md）
- UPDATE_SUMMARY.md - 配置更新总结
- BILINGUAL_DOCS.md - 双语文档说明
- BILINGUAL_IMPLEMENTATION.md - 双语实施报告
- 英文版的内部文档（保留中文版在 internal/）

## 访问指南

### 用户
从这里开始：
1. [README.md](../README.md) 或 [README.en.md](../README.en.md)
2. [HOW_TO_RUN.md](../HOW_TO_RUN.md)
3. [docs/index.md](../docs/index.md)

### 开发者
内部文档入口：
1. [docs/internal/requirements.md](../docs/internal/requirements.md)
2. [docs/internal/architecture.md](../docs/internal/architecture.md)
3. [docs/internal/development_plan.md](../docs/internal/development_plan.md)

## 文档维护

### 添加新用户文档
1. 在 `docs/zh/` 创建中文版
2. 在 `docs/en/` 创建英文版
3. 更新 `docs/index.md`

### 添加新内部文档
1. 在 `docs/internal/` 创建文档
2. 更新 `docs/index.md` 的内部文档部分

### 归档文档
将不再需要的过程文档移到 `archive/` 目录

## 整理记录

**整理前**: 25+ markdown文件散落各处
**整理后**:
- 用户文档: 8个（含索引）
- 内部文档: 5个
- 根目录: 4个
- 归档: 11个

**删除**: 无（全部归档保留）
**新增**:
- docs/internal/development_plan.md（整合自 NEXT_STEPS.md）
- 更新的 docs/index.md
