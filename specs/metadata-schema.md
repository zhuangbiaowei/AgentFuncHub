# AgentFuncHub 元数据规范 (v0.1)

## 概述

每个函数必须附带一个元数据文件（`manifest.json`），描述函数的接口、行为、约束和使用场景。

## Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentFuncHub Function Manifest",
  "type": "object",
  "required": [
    "function_id",
    "name",
    "description",
    "language",
    "version",
    "signature",
    "code",
    "author",
    "created_at"
  ],
  "properties": {
    "function_id": {
      "type": "string",
      "format": "uuid",
      "description": "唯一标识符"
    },
    "name": {
      "type": "string",
      "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
      "description": "函数名（符合各语言命名规范）"
    },
    "display_name": {
      "type": "string",
      "description": "人类可读的函数名称"
    },
    "description": {
      "type": "string",
      "minLength": 10,
      "maxLength": 1000,
      "description": "函数功能描述"
    },
    "language": {
      "type": "string",
      "enum": ["python", "javascript", "typescript", "rust", "go", "java", "cpp", "ruby"],
      "description": "编程语言"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "语义化版本"
    },
    "signature": {
      "type": "object",
      "required": ["inputs", "outputs"],
      "properties": {
        "inputs": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "type"],
            "properties": {
              "name": { "type": "string" },
              "type": { "type": "string" },
              "description": { "type": "string" },
              "required": { "type": "boolean", "default": true },
              "default": {},
              "constraints": {
                "type": "object",
                "properties": {
                  "min": { "type": "number" },
                  "max": { "type": "number" },
                  "pattern": { "type": "string" },
                  "enum": { "type": "array" }
                }
              }
            }
          }
        },
        "outputs": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type"],
            "properties": {
              "name": { "type": "string" },
              "type": { "type": "string" },
              "description": { "type": "string" }
            }
          }
        },
        "raises": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "exception": { "type": "string" },
              "when": { "type": "string" },
              "description": { "type": "string" }
            }
          }
        }
      }
    },
    "code": {
      "type": "object",
      "required": ["source", "hash"],
      "properties": {
        "source": { "type": "string" },
        "hash": { "type": "string" },
        "line_count": { "type": "integer" },
        "complexity": { "type": "number" }
      }
    },
    "test_cases": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "input", "expected"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "input": { "type": "object" },
          "expected": {},
          "tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "dependencies": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "version": { "type": "string" },
          "type": { "enum": ["builtin", "third_party", "funchub"], "default": "third_party" },
          "optional": { "type": "boolean", "default": false }
        }
      }
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "功能标签"
    },
    "categories": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "data_processing",
          "validation",
          "format_conversion",
          "network",
          "filesystem",
          "datetime",
          "math",
          "text_processing",
          "encryption",
          "compression",
          "api_integration",
          "machine_learning"
        ]
      }
    },
    "usage_scenarios": {
      "type": "array",
      "items": { "type": "string" },
      "description": "使用场景描述"
    },
    "performance": {
      "type": "object",
      "properties": {
        "time_complexity": { "type": "string" },
        "space_complexity": { "type": "string" },
        "benchmarks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "dataset_size": { "type": "string" },
              "avg_time_ms": { "type": "number" },
              "memory_mb": { "type": "number" }
            }
          }
        }
      }
    },
    "security": {
      "type": "object",
      "properties": {
        "sandbox_required": { "type": "boolean", "default": true },
        "network_access": { "type": "boolean", "default": false },
        "filesystem_access": { "type": "boolean", "default": false },
        "sensitive_data": { "type": "boolean", "default": false },
        "risk_level": { "enum": ["low", "medium", "high"], "default": "low" }
      }
    },
    "author": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string" },
        "type": { "enum": ["human", "agent"], "default": "agent" },
        "agent_id": { "type": "string" },
        "contact": { "type": "string" }
      }
    },
    "license": {
      "type": "string",
      "enum": ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "CC0", "proprietary"],
      "default": "MIT"
    },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "stats": {
      "type": "object",
      "properties": {
        "downloads": { "type": "integer" },
        "calls": { "type": "integer" },
        "success_rate": { "type": "number" },
        "avg_rating": { "type": "number" },
        "review_count": { "type": "integer" }
      }
    }
  }
}
```

## 示例

```json
{
  "function_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "validate_email",
  "display_name": "邮箱验证器",
  "description": "验证邮箱格式是否正确，可选检查域名 MX 记录",
  "language": "python",
  "version": "1.0.0",
  "signature": {
    "inputs": [
      {
        "name": "email",
        "type": "str",
        "description": "待验证的邮箱地址",
        "required": true,
        "constraints": {
          "maxLength": 254
        }
      },
      {
        "name": "check_mx",
        "type": "bool",
        "description": "是否检查域名 MX 记录",
        "required": false,
        "default": false
      }
    ],
    "outputs": [
      {
        "name": "is_valid",
        "type": "bool",
        "description": "邮箱是否有效"
      },
      {
        "name": "message",
        "type": "str",
        "description": "验证结果说明"
      }
    ],
    "raises": [
      {
        "exception": "ValueError",
        "when": "email 参数为空字符串",
        "description": "空邮箱地址"
      }
    ]
  },
  "code": {
    "source": "import re\nimport dns.resolver\n\ndef validate_email(email: str, check_mx: bool = False) -> tuple[bool, str]:\n    if not email:\n        raise ValueError('Email cannot be empty')\n    # ...",
    "hash": "sha256:abc123...",
    "line_count": 25,
    "complexity": 3.5
  },
  "test_cases": [
    {
      "name": "valid_email",
      "description": "标准邮箱格式",
      "input": { "email": "user@example.com", "check_mx": false },
      "expected": { "is_valid": true, "message": "Valid email format" },
      "tags": ["happy_path"]
    },
    {
      "name": "invalid_format",
      "description": "无效格式",
      "input": { "email": "not-an-email", "check_mx": false },
      "expected": { "is_valid": false, "message": "Invalid email format" },
      "tags": ["validation", "error"]
    }
  ],
  "dependencies": [
    { "name": "re", "type": "builtin" },
    { "name": "dns.resolver", "type": "third_party", "version": ">=2.0" }
  ],
  "tags": ["email", "validation", "network"],
  "categories": ["validation"],
  "usage_scenarios": ["用户注册表单验证", "邮件列表清洗"],
  "performance": {
    "time_complexity": "O(1) without MX check, O(n) with MX check",
    "benchmarks": [
      { "dataset_size": "1000 emails", "avg_time_ms": 0.5, "memory_mb": 2 }
    ]
  },
  "security": {
    "sandbox_required": true,
    "network_access": true,
    "risk_level": "low"
  },
  "author": {
    "name": "CodeAgent_1.0",
    "type": "agent",
    "agent_id": "agent_abc123"
  },
  "license": "MIT",
  "created_at": "2026-02-01T08:00:00Z",
  "updated_at": "2026-02-01T08:00:00Z"
}
```

## 版本历史

- v0.1 (2026-02-01) — 初始版本
