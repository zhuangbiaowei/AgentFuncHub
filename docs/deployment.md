# 部署指南

## 快速开始 (Docker Compose)

### 1. 克隆仓库

```bash
git clone https://github.com/zhuangbiaowei/AgentFuncHub.git
cd AgentFuncHub
```

### 2. 配置环境变量

创建 `.env` 文件:

```bash
# JWT 密钥 (生产环境请使用强密码)
JWT_SECRET_KEY=your-secret-key

# GitHub OAuth (可选)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### 3. 启动服务

```bash
docker-compose up -d
```

服务将启动在:
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000

### 4. 查看日志

```bash
# 所有服务
docker-compose logs -f

# 仅后端
docker-compose logs -f backend

# 仅前端
docker-compose logs -f frontend
```

### 5. 停止服务

```bash
docker-compose down
```

## 生产部署

### 使用 PostgreSQL

编辑 `docker-compose.yml`，取消数据库部分的注释:

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: agentfunchub
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: agentfunchub
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    # ...
    environment:
      - DATABASE_URL=postgresql://agentfunchub:${DB_PASSWORD}@db:5432/agentfunchub
      - USE_SQLITE=false
    depends_on:
      - db

volumes:
  postgres_data:
```

### 使用 Docker Swarm

```bash
# 初始化 swarm
docker swarm init

# 部署
docker stack deploy -c docker-compose.yml agentfunchub

# 查看服务
docker service ls

# 扩展后端服务
docker service scale agentfunchub_backend=3
```

### 使用 Kubernetes

参考 `deploy/k8s/` 目录中的配置。

## GitHub OAuth 配置

1. 访问 GitHub Settings -> Developer settings -> OAuth Apps
2. 创建新的 OAuth App
3. 填写信息:
   - Application name: AgentFuncHub
   - Homepage URL: http://localhost:3000
   - Authorization callback URL: http://localhost:8000/auth/github/callback
4. 复制 Client ID 和 Client Secret 到 `.env` 文件

## SSL/HTTPS (生产)

### 使用 Nginx + Let's Encrypt

```nginx
server {
    listen 443 ssl http2;
    server_name api.agentfunchub.io;

    ssl_certificate /etc/letsencrypt/live/api.agentfunchub.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.agentfunchub.io/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 使用 Traefik

```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt

  backend:
    # ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.agentfunchub.io`)"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
```

## 监控

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 前端健康检查
curl http://localhost:3000
```

### 日志收集

```bash
# 使用 Loki + Grafana
docker-compose -f docker-compose.logging.yml up -d
```

### 指标监控

后端暴露 Prometheus 指标:

```
GET /metrics
```

## 备份

### 备份 SQLite 数据库

```bash
# 复制数据文件
cp data/agentfunchub.db backup/agentfunchub-$(date +%Y%m%d).db
```

### 备份 PostgreSQL

```bash
# 使用 pg_dump
docker-compose exec db pg_dump -U agentfunchub agentfunchub > backup.sql
```

## 故障排除

### 后端无法启动

```bash
# 检查日志
docker-compose logs backend

# 检查端口占用
lsof -i :8000

# 重新构建
docker-compose build --no-cache backend
```

### 前端无法连接后端

1. 检查 CORS 配置
2. 确认 API URL 设置正确
3. 检查网络连接

```bash
# 测试后端连通性
curl http://localhost:8000/
```

## 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 数据库迁移 (如需要)
docker-compose exec backend alembic upgrade head
```
