# AgentFuncHub 开发计划

> 项目仓库: https://github.com/zhuangbiaowei/AgentFuncHub  
> 当前阶段: Phase 1 - 概念验证 (2-4周)  
> 更新日期: 2026-02-01

---

## 本周目标 (Week 1)

### Day 1-2: 完善基础架构
- [x] 创建项目骨架
- [x] 提交初始代码到 GitHub
- [ ] 添加 .gitignore 和 LICENSE
- [ ] 创建 requirements.txt
- [ ] 设置 pytest 测试框架

### Day 3-4: 扩展示例函数 (目标: 10个)
- [ ] 数据验证类 (3个): 手机号、身份证号、IP地址
- [ ] 文本处理类 (3个): 分词、摘要、关键词提取
- [ ] 日期时间类 (2个): 日期解析、时间格式化
- [ ] 格式转换类 (2个): JSON修复、编码转换

### Day 5-7: 后端原型
- [ ] 搭建 FastAPI 基础框架
- [ ] 实现函数存储 API (CRUD)
- [ ] 实现基础的向量搜索 (使用简单的余弦相似度)
- [ ] 实现函数验证引擎 (执行测试用例)

---

## Phase 1 完整目标

### 功能目标
1. **元数据 Schema 定稿** - 支持所有常见函数描述场景
2. **30个示例函数** - 覆盖验证、文本、日期、数学、网络等类别
3. **语义搜索原型** - 基于向量相似度的函数检索
4. **验证引擎** - 自动执行测试用例并报告结果
5. **API 文档** - 完整的接口文档和使用示例

### 技术目标
- 代码覆盖率 > 80%
- API 响应时间 < 500ms
- 搜索准确率 > 70% (人工评估)

---

## 提交计划

| 时间 | 提交内容 | Commit Message |
|------|----------|----------------|
| Day 1 | 项目配置 | `chore: add project configuration files` |
| Day 2 | 示例函数集 | `feat: add 10 example functions` |
| Day 3 | FastAPI 框架 | `feat: setup FastAPI backend structure` |
| Day 4 | 存储层 | `feat: implement function storage API` |
| Day 5 | 搜索功能 | `feat: implement semantic search prototype` |
| Day 6 | 验证引擎 | `feat: add function validation engine` |
| Day 7 | 文档更新 | `docs: update README and API docs` |

---

## 开发日志

### 2026-02-01
- ✅ 初始化项目
- ✅ 创建核心文档 (README, vision, roadmap, FAQ)
- ✅ 编写元数据 Schema
- ✅ 创建 2 个示例函数
- ✅ 编写 Python SDK 原型
- ✅ 推送到 GitHub

