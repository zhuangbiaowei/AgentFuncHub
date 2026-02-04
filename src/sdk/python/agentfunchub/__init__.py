"""
AgentFuncHub Python SDK

让 Python 开发者轻松使用 AgentFuncHub 的函数库。

示例:
    >>> from agentfunchub import Client
    >>> client = Client()
    >>> 
    >>> # 搜索函数
    >>> results = client.search("验证邮箱")
    >>> 
    >>> # 执行函数
    >>> result = client.call("validation.email.basic", email="test@example.com")
"""

__version__ = "0.1.0"
__author__ = "AgentFuncHub Team"

from .client import Client
from .async_client import AsyncClient
from .function import Function
from .exceptions import (
    AgentFuncHubError,
    AuthenticationError,
    FunctionNotFoundError,
    ExecutionError,
    ValidationError,
)

__all__ = [
    "Client",
    "AsyncClient",
    "Function",
    "AgentFuncHubError",
    "AuthenticationError",
    "FunctionNotFoundError",
    "ExecutionError",
    "ValidationError",
]
