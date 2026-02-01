# 贡献指南

感谢你对 AgentFuncHub 的兴趣！本文档将帮助你快速开始贡献。

## 如何贡献

### 1. 贡献示例函数

这是目前最需要的贡献！创建一个新函数只需几个步骤：

#### 步骤

1. **创建目录**
   ```bash
   mkdir examples/your_function_name
   ```

2. **编写 manifest.json**
   
   参考现有函数的格式，必须包含：
   - 函数基本信息（name, description, language）
   - 完整的签名（inputs, outputs）
   - 至少 3 个测试用例
   - 安全性声明

3. **测试你的函数**
   ```bash
   python scripts/validate_function.py examples/your_function_name/manifest.json
   ```

4. **提交 PR**
   - 函数名称使用小写和下划线
   - 提供清晰的描述
   - 确保测试通过

#### 函数命名规范

- 使用动词开头：`validate_`, `parse_`, `generate_`, `format_`
- 使用小写和下划线：`validate_email`, `parse_csv`
- 添加语言/地区后缀（如果需要）：`validate_phone_cn`

#### 测试用例要求

每个函数至少包含：
- 1 个正常路径（happy_path）
- 1 个错误处理（error）
- 1 个边界情况（edge_case）

### 2. 贡献代码

#### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/zhuangbiaowei/AgentFuncHub.git
cd AgentFuncHub

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/
```

#### 代码风格

- 使用 Black 格式化：`black src/`
- 类型注解：所有函数参数和返回值
- 文档字符串：Google 风格

### 3. 报告问题

发现 bug 或有新想法？请提交 Issue：

- **Bug 报告**：描述重现步骤、期望行为、实际行为
- **功能请求**：描述使用场景和预期效果
- **文档改进**：指出错误或不足

## 项目结构

```
AgentFuncHub/
├── docs/           # 文档
├── examples/       # 示例函数
│   └── function_name/
│       └── manifest.json
├── specs/          # 技术规范
├── src/            # 源代码
│   ├── server/     # 后端服务
│   └── sdk/        # SDK
├── tests/          # 测试
└── scripts/        # 工具脚本
```

## 开发路线图

### Phase 1: 概念验证（当前）
- [x] 基础架构
- [x] 示例函数
- [ ] 完善验证引擎
- [ ] API 测试

### Phase 2: MVP
- [ ] 数据库迁移（PostgreSQL）
- [ ] 用户认证
- [ ] 函数调用沙箱

### Phase 3: 社区
- [ ] Web 界面
- [ ] 评分系统
- [ ] 函数市场

### Phase 4: 生产
- [ ] 企业版功能
- [ ] 性能优化
- [ ] SLA 保证

## 联系方式

- GitHub Issues: [提交问题](https://github.com/zhuangbiaowei/AgentFuncHub/issues)
- 项目负责人：庄表伟
- AI 助手：AI学徒 1.0

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**感谢你的贡献！** 🎉
