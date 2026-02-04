# AgentFuncHub 后端 Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/server/ ./src/server/
COPY examples/ ./examples/

# 设置环境变量
ENV PYTHONPATH=/app/src/server
ENV USE_SQLITE=true
ENV JWT_SECRET_KEY=change-in-production

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
