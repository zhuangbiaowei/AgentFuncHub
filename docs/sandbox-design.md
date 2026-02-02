# AgentFuncHub 沙箱执行器设计

> 函数执行环境的安全隔离方案

---

## 1. 设计目标

### 核心需求
- **安全隔离**: 函数代码在隔离环境中执行，不能访问宿主机资源
- **资源限制**: 限制 CPU、内存、执行时间
- **输入/输出**: 安全地传递参数和获取结果
- **错误处理**: 优雅处理执行错误和超时

### 非功能性需求
- **性能**: 冷启动 < 3s，热执行 < 500ms
- **可扩展性**: 支持并发执行
- **可观测性**: 执行日志和监控

---

## 2. 方案对比

| 方案 | 隔离级别 | 启动时间 | 资源控制 | 复杂度 | 适用场景 |
|------|---------|---------|---------|--------|----------|
| **Docker** | 进程级 | 1-3s | 优秀 | 中 | 通用，推荐 |
| **Firecracker** | VM 级 | 100ms | 优秀 | 高 | 高安全要求 |
| **gVisor** | 系统调用过滤 | 500ms | 优秀 | 高 | 额外安全层 |
| **Restricted Python** | 语言级 | 即时 | 有限 | 低 | 简单函数 |

### 选择: Docker + Restricted Python

**理由**:
1. Docker 是成熟的容器技术，易于部署
2. 资源限制通过 cgroup 实现
3. 可以灵活配置 Python 运行时
4. 开发成本低

**改进**: 未来可添加 gVisor 作为额外安全层

---

## 3. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    API 服务 (FastAPI)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Execute   │──►│   Sandbox   │──►│   Docker Engine    │  │
│  │   Endpoint  │  │   Manager   │  │   (via socket)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP / Unix Socket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Docker 守护进程                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Function Execution Container               ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │   Python    │  │  Memory     │  │   CPU       │    ││
│  │  │  Runtime    │  │  Limit      │  │   Limit     │    ││
│  │  │  (3.10+)    │  │  (512MB)    │  │   (1 core)  │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  │                                                         ││
│  │  ┌─────────────┐  ┌─────────────┐                     ││
│  │  │   Input     │  │   Output    │                     ││
│  │  │   (JSON)    │──►│   (JSON)    │                     ││
│  │  └─────────────┘  └─────────────┘                     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 执行流程

### 4.1 同步执行

```
1. API 接收执行请求
   POST /functions/{id}/execute
   Body: { "input": { "email": "test@example.com" } }

2. 从数据库获取函数代码
   SELECT entrypoint_code FROM functions WHERE spec_id = '...'

3. 创建执行环境
   - 生成唯一执行 ID
   - 准备输入数据 (JSON)
   - 构建 Docker 容器

4. 在沙箱中执行
   docker run --rm \
     --memory=512m \
     --cpus=1.0 \
     --timeout=30 \
     function-executor \
     python /app/execute.py

5. 收集结果
   - 解析输出 JSON
   - 记录执行时间
   - 捕获错误

6. 返回响应
   {
     "success": true,
     "result": { "is_valid": true },
     "duration_ms": 45
   }
```

### 4.2 异步执行 (未来)

```
1. 提交执行任务 → 返回任务 ID
2. 后台 Worker 执行
3. Webhook 或轮询获取结果
```

---

## 5. 安全策略

### 5.1 容器限制

```dockerfile
# 限制资源
--memory=512m          # 内存限制
--memory-swap=512m     # 禁止 swap
--cpus=1.0             # CPU 限制
--pids-limit=100       # 进程数限制

# 禁止特权
--security-opt=no-new-privileges
--cap-drop=ALL

# 只读文件系统
--read-only
--tmpfs /tmp:noexec,nosuid,size=100m

# 网络隔离 (可选)
--network=none
```

### 5.2 Python 限制

```python
# 禁止危险操作
import sys
sys.modules['os'] = None
sys.modules['subprocess'] = None
sys.modules['socket'] = None

# 限制执行时间
import signal
signal.alarm(30)  # 30 秒超时
```

### 5.3 输入验证

- 严格验证输入参数类型
- 限制输入数据大小 (1MB)
- 防止序列化攻击

---

## 6. 错误处理

| 错误类型 | 说明 | 返回状态 |
|---------|------|---------|
| `success` | 执行成功 | 200 |
| `timeout` | 执行超时 (>30s) | 408 |
| `memory_exceeded` | 内存超限 | 507 |
| `runtime_error` | 代码运行时错误 | 500 |
| `invalid_input` | 输入参数无效 | 400 |
| `not_found` | 函数不存在 | 404 |

---

## 7. 性能优化

### 7.1 容器预热

- 保持基础容器镜像运行
- 使用容器池减少启动时间

### 7.2 缓存策略

- 缓存函数代码解析结果
- 复用已安装的依赖

### 7.3 资源池

```python
# 容器池示例
class ContainerPool:
    def __init__(self, size=5):
        self.pool = Queue(maxsize=size)
        self._fill_pool()
    
    def get(self):
        return self.pool.get()
    
    def put(self, container):
        self.pool.put(container)
```

---

## 8. 监控和日志

### 8.1 执行指标

- 执行次数
- 平均执行时间
- 错误率
- 资源使用率

### 8.2 日志记录

```json
{
  "execution_id": "uuid",
  "function_id": "validation.email.basic",
  "status": "success",
  "duration_ms": 45,
  "memory_mb": 128,
  "input": { "email": "test@example.com" },
  "output": { "is_valid": true },
  "created_at": "2026-02-02T10:00:00Z"
}
```

---

## 9. API 设计

### 9.1 执行端点

```http
POST /functions/{function_id}/execute
Content-Type: application/json

{
  "input": {
    "email": "test@example.com"
  },
  "timeout": 30,
  "async": false
}
```

**响应**:
```json
{
  "success": true,
  "execution_id": "uuid",
  "function_id": "validation.email.basic",
  "status": "success",
  "result": {
    "is_valid": true,
    "message": "Valid email format"
  },
  "duration_ms": 45,
  "memory_mb": 32,
  "created_at": "2026-02-02T10:00:00Z"
}
```

### 9.2 批量执行 (未来)

```http
POST /functions/{function_id}/batch
Content-Type: application/json

{
  "inputs": [
    { "email": "test1@example.com" },
    { "email": "test2@example.com" }
  ]
}
```

---

## 10. 实现计划

### Day 5: 基础沙箱
- [ ] 创建 Docker 执行器类
- [ ] 实现基础执行流程
- [ ] 添加资源限制

### Day 6: 执行 API
- [ ] 创建执行端点
- [ ] 集成数据库
- [ ] 错误处理和日志

### Day 7: 测试和优化
- [ ] 执行测试
- [ ] 性能测试
- [ ] 安全测试

---

*设计日期: 2026-02-02*
