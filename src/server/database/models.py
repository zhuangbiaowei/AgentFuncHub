"""
AgentFuncHub 数据库模型
SQLAlchemy 2.0 风格
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Boolean, 
    Integer, DECIMAL, ForeignKey, JSON, ARRAY, Index, UniqueConstraint,
    event
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, INET
from sqlalchemy.orm import DeclarativeBase, relationship, Session
from sqlalchemy.sql import func
import uuid


class Base(DeclarativeBase):
    """基础模型类"""
    pass


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    github_id = Column(String(100), unique=True, nullable=True)
    api_key = Column(String(64), unique=True, nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    functions = relationship("Function", back_populates="owner")
    executions = relationship("Execution", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Function(Base):
    """函数模型"""
    __tablename__ = "functions"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spec_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # 所有者
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # 基本信息
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    
    # 语言和运行时
    language = Column(String(50), nullable=False, index=True)
    runtime = Column(String(100), nullable=True)
    
    # 完整 FunctionSpec JSON
    spec_json = Column(JSON, nullable=False)
    
    # 入口点信息
    entrypoint_kind = Column(String(20), nullable=False)  # inline, file, container, wasm
    entrypoint_symbol = Column(String(255), nullable=False)
    entrypoint_code = Column(Text, nullable=True)
    
    # 签名信息
    signature_inputs = Column(JSON, default={})
    signature_outputs = Column(JSON, default={})
    
    # 语义信息
    semantics_deterministic = Column(Boolean, default=True)
    semantics_side_effects = Column(JSON, default=["none"])
    semantics_purity = Column(String(20), default="pure")
    semantics_security = Column(JSON, default={})
    
    # 标签 (GIN 索引)
    tags = Column(ARRAY(String), default=[], index=True)
    
    # 搜索文本 (全文搜索)
    search_text = Column(TSVECTOR, nullable=True)
    
    # 向量嵌入 (需要 pgvector 扩展)
    # 注意: 需要先安装 pgvector: CREATE EXTENSION vector;
    # embedding = Column(Vector(384), nullable=True)
    
    # 统计信息
    view_count = Column(Integer, default=0)
    call_count = Column(Integer, default=0)
    rating_avg = Column(DECIMAL(3, 2), default=0.00)
    rating_count = Column(Integer, default=0)
    
    # 质量信息
    quality_maturity = Column(String(20), default="experimental")
    quality_coverage = Column(DECIMAL(3, 2), default=0.00)
    
    # 许可证和溯源
    license = Column(String(50), default="MIT")
    provenance_created_at = Column(DateTime(timezone=True), nullable=True)
    provenance_updated_at = Column(DateTime(timezone=True), nullable=True)
    provenance_source_kind = Column(String(50), nullable=True)  # manual, agent, imported
    
    # 元数据
    is_public = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    owner = relationship("User", back_populates="functions")
    executions = relationship("Execution", back_populates="function")
    ratings = relationship("Rating", back_populates="function")
    versions = relationship("FunctionVersion", back_populates="function")
    
    # 索引
    __table_args__ = (
        Index('idx_functions_search', 'search_text', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<Function(spec_id={self.spec_id}, name={self.name})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "spec_id": self.spec_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "language": self.language,
            "runtime": self.runtime,
            "spec_json": self.spec_json,
            "tags": self.tags,
            "view_count": self.view_count,
            "call_count": self.call_count,
            "rating_avg": float(self.rating_avg) if self.rating_avg else 0.0,
            "quality": {
                "maturity": self.quality_maturity,
                "coverage": float(self.quality_coverage) if self.quality_coverage else 0.0
            },
            "license": self.license,
            "is_public": self.is_public,
            "is_deprecated": self.is_deprecated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Execution(Base):
    """执行记录模型"""
    __tablename__ = "executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    function_id = Column(UUID(as_uuid=True), ForeignKey("functions.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # 执行状态
    status = Column(String(20), nullable=False, index=True)  # pending, running, success, error, timeout
    
    # 输入输出
    input_data = Column("input", JSON, nullable=True)
    output_data = Column("output", JSON, nullable=True)
    
    # 性能指标
    duration_ms = Column(Integer, nullable=True)
    memory_mb = Column(Integer, nullable=True)
    
    # 错误信息
    error_type = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # 沙箱信息
    sandbox_id = Column(String(100), nullable=True)
    sandbox_logs = Column(Text, nullable=True)
    
    # 元数据
    client_ip = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    function = relationship("Function", back_populates="executions")
    user = relationship("User", back_populates="executions")
    
    def __repr__(self):
        return f"<Execution(id={self.id}, status={self.status})>"


class FunctionVersion(Base):
    """函数版本历史"""
    __tablename__ = "function_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    function_id = Column(UUID(as_uuid=True), ForeignKey("functions.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    spec_json = Column(JSON, nullable=False)
    change_notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    function = relationship("Function", back_populates="versions")
    
    # 唯一约束: 每个函数版本唯一
    __table_args__ = (
        UniqueConstraint('function_id', 'version', name='uix_function_version'),
    )
    
    def __repr__(self):
        return f"<FunctionVersion(function_id={self.function_id}, version={self.version})>"


class Rating(Base):
    """评分模型"""
    __tablename__ = "ratings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    function_id = Column(UUID(as_uuid=True), ForeignKey("functions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    function = relationship("Function", back_populates="ratings")
    user = relationship("User", back_populates="ratings")
    
    # 唯一约束: 每个用户只能评分一次
    __table_args__ = (
        UniqueConstraint('function_id', 'user_id', name='uix_function_user_rating'),
    )
    
    def __repr__(self):
        return f"<Rating(function_id={self.function_id}, user_id={self.user_id}, rating={self.rating})>"


# 事件监听: 自动更新 search_text
@event.listens_for(Function, 'before_insert')
@event.listens_for(Function, 'before_update')
def update_search_text(mapper, connection, target):
    """在插入/更新时自动生成 search_text"""
    # 提取用于全文搜索的文本
    parts = [
        target.name or "",
        target.description or "",
        " ".join(target.tags or []),
        target.spec_id or ""
    ]
    
    # 从 signature 中提取参数名
    if target.signature_inputs:
        for param_name in target.signature_inputs.keys():
            parts.append(param_name)
    if target.signature_outputs:
        for param_name in target.signature_outputs.keys():
            parts.append(param_name)
    
    search_content = " ".join(filter(None, parts))
    
    # 使用 to_tsvector (需要在数据库中执行)
    # 这里只是设置标记，真正的转换在数据库层完成
    target.search_text_content = search_content


def create_tables(engine):
    """创建所有表"""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """删除所有表"""
    Base.metadata.drop_all(engine)
