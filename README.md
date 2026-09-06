# 宠物准入信息平台 / Place Animal Access Map

这是 ZCode 从空目录开工的启动包。

## 用法

1. 解压本 ZIP 到空目录。
2. 用 ZCode 打开目录。
3. 将 `ZCODE_START_PROMPT.md` 全文粘给 ZCode。
4. 不需要你先建脚手架，让 Agent 按 GOAL 连续执行。

## 唯一设计母版
`docs/MASTER_DESIGN_v0.3_DEV.md`

## 控制文件
- AGENTS.md
- GOAL.md
- DECISIONS.md
- IMPLEMENTATION_PLAN.md
- ACCEPTANCE_MATRIX.md
- PROJECT_STATE.md
- BLOCKERS.md

## 冻结技术栈
- Client: uni-app x + Vue 3 + TypeScript
- Admin: Vue 3 + TypeScript + Vite
- API: FastAPI
- DB: PostgreSQL + PostGIS
- Redis + Celery
- MinIO/S3
- Map provider adapter; Tencent first
- AI provider adapter; Mock first

## 基础环境

Windows:
```powershell
Copy-Item .env.example .env
docker compose up -d
```

macOS/Linux:
```bash
cp .env.example .env
docker compose up -d
```

真正的项目脚手架和验证由 ZCode Phase 0 完成。
