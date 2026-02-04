"""
SDK 异常定义
"""


class AgentFuncHubError(Exception):
    """基础异常"""
    pass


class AuthenticationError(AgentFuncHubError):
    """认证失败"""
    pass


class FunctionNotFoundError(AgentFuncHubError):
    """函数不存在"""
    pass


class ExecutionError(AgentFuncHubError):
    """函数执行失败"""
    
    def __init__(self, message: str, error_type: str = None, details: dict = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}


class ValidationError(AgentFuncHubError):
    """参数验证失败"""
    pass


class RateLimitError(AgentFuncHubError):
    """速率限制"""
    pass
