# AgentFuncHub 项目状态

## 创建时间
2026-02-01

## 当前状态
🚧 概念验证阶段 (Phase 1)

## 已完成工作

### 文档 (docs/)
- ✅ README.md — 项目总览与快速开始
- ✅ vision.md — 项目愿景与设计原则
- ✅ roadmap.md — 四阶段路线图
- ✅ faq.md — 常见问题解答

### 规范 (specs/)
- ✅ metadata-schema.md — 函数元数据完整 Schema
- ✅ api-spec.md — REST API 接口规范

### 代码 (src/)
- ✅ sdk/python/agentfunchub.py — Python SDK 原型

### 示例 (examples/)
- ✅ validate_email/manifest.json — 邮箱验证函数
- ✅ generate_slug/manifest.json — URL slug 生成函数

### 测试 (tests/)
- ✅ test_sdk.py — SDK 和 Schema 测试

## 目录结构

```
~/AgentFuncHub/
├── README.md
├── docs/
│   ├── vision.md
│   ├── roadmap.md
│   └── faq.md
├── specs/
│   ├── metadata-schema.md
│   └── api-spec.md
├── src/
│   └── sdk/
│       └── python/
│           └── agentfunchub.py
├── examples/
│   ├── validate_email/
│   │   └── manifest.json
│   └── generate_slug/
│       └── manifest.json
└── tests/
    └── test_sdk.py
```

## 下一步行动

### 本周 (P0)
- [ ] 完善元数据 Schema（添加更多字段说明）
- [ ] 创建 5-10 个更多示例函数
- [ ] 设计函数验证引擎原型

### 本月 (P1)
- [ ] 搭建后端服务框架（FastAPI）
- [ ] 选择并配置向量数据库
- [ ] 实现基础搜索功能

### 待讨论
- [ ] 项目名称是否合适？（AgentFuncHub vs FuncHub vs CodeCell）
- [ ] 技术栈选择（Python vs Node.js）
- [ ] 是否开源，以及开源协议
- [ ] 如何冷启动（先有函数还是先有用户？）

## 关键决策点

| 决策 | 当前倾向 | 需要确认 |
|------|----------|----------|
| 后端语言 | Python/FastAPI | 是否有 Node.js 偏好？ |
| 向量数据库 | Pinecone/Weaviate | 是否接受云服务？ |
| 沙箱技术 | Docker/Firecracker | 资源限制？ |
| 嵌入模型 | OpenAI/本地 | 成本 vs 隐私？ |

## 资源需求

### 技术资源
- 后端服务器
- 向量数据库
- 沙箱执行环境

### 人力资源
- 后端开发
- 前端开发（Web 界面）
- 社区运营

### 时间投入
- MVP：1-2 个月（兼职）
- 生产就绪：6-12 个月

## 联系

项目负责人：庄表伟
AI 助手：AI学徒 1.0

---

*最后更新：2026-02-01*
