#!/usr/bin/env python3
"""
FunctionSpec 验证工具

验证 function.yaml 是否符合 FunctionSpec v0.1 规范

用法:
    python validate_spec.py <function_directory>
    python validate_spec.py --all
    python validate_spec.py --json <function_directory>
"""

import sys
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    ERROR = "ERROR"      # MUST 字段缺失或无效
    WARNING = "WARNING"  # SHOULD 字段缺失
    INFO = "INFO"        # MAY 字段建议


@dataclass
class ValidationIssue:
    severity: Severity
    field: str
    message: str
    suggestion: str = ""


@dataclass
class ValidationResult:
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, field: str, message: str, suggestion: str = ""):
        self.issues.append(ValidationIssue(Severity.ERROR, field, message, suggestion))
        self.valid = False
    
    def add_warning(self, field: str, message: str, suggestion: str = ""):
        self.issues.append(ValidationIssue(Severity.WARNING, field, message, suggestion))
    
    def add_info(self, field: str, message: str, suggestion: str = ""):
        self.issues.append(ValidationIssue(Severity.INFO, field, message, suggestion))


class FunctionSpecValidator:
    """FunctionSpec v0.1 验证器"""
    
    VALID_TYPES = [
        "string", "integer", "number", "boolean",
        "object", "array", "bytes", "file", "path", "any"
    ]
    
    VALID_SIDE_EFFECTS = [
        "none", "fs_read", "fs_write", "network",
        "process_spawn", "db_read", "db_write",
        "env_read", "stdout", "stderr", "ipc", "gpu"
    ]
    
    VALID_ENTRYPOINT_KINDS = ["file", "inline", "container", "wasm"]
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """验证单个 function.yaml 文件"""
        result = ValidationResult(valid=True)
        
        # 检查文件存在
        if not file_path.exists():
            result.add_error("file", f"File not found: {file_path}")
            return result
        
        # 读取 YAML
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
        except yaml.YAMLError as e:
            result.add_error("yaml", f"Invalid YAML format: {e}")
            return result
        except Exception as e:
            result.add_error("file", f"Failed to read file: {e}")
            return result
        
        if spec is None:
            result.add_error("yaml", "Empty YAML file")
            return result
        
        # 验证各个部分
        self._validate_spec_version(spec, result)
        self._validate_identity(spec, result)
        self._validate_language(spec, result)
        self._validate_entrypoint(spec, result)
        self._validate_signature(spec, result)
        self._validate_semantics(spec, result)
        self._validate_tests(spec, result)
        self._validate_optional(spec, result)
        
        # 统计信息
        result.stats = {
            "total_issues": len(result.issues),
            "errors": len([i for i in result.issues if i.severity == Severity.ERROR]),
            "warnings": len([i for i in result.issues if i.severity == Severity.WARNING]),
            "infos": len([i for i in result.issues if i.severity == Severity.INFO]),
        }
        
        return result
    
    def _validate_spec_version(self, spec: Dict, result: ValidationResult):
        """验证 spec_version"""
        if "spec_version" not in spec:
            result.add_error(
                "spec_version",
                "Missing required field: spec_version",
                'Add: spec_version: "0.1"'
            )
        elif spec["spec_version"] != "0.1":
            result.add_warning(
                "spec_version",
                f"Unknown spec version: {spec['spec_version']}",
                'Should be: "0.1"'
            )
    
    def _validate_identity(self, spec: Dict, result: ValidationResult):
        """验证身份信息"""
        # id (MUST)
        if "id" not in spec:
            result.add_error("id", "Missing required field: id")
        else:
            id_val = spec["id"]
            if not re.match(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$', id_val):
                result.add_warning(
                    "id",
                    f"ID format should be dot-notation: {id_val}",
                    "Example: validation.email.basic"
                )
        
        # version (MUST)
        if "version" not in spec:
            result.add_error("version", "Missing required field: version")
        else:
            version = spec["version"]
            if not re.match(r'^\d+\.\d+\.\d+$', version):
                result.add_warning(
                    "version",
                    f"Version should follow SemVer: {version}",
                    "Example: 1.0.0"
                )
        
        # name (MUST)
        if "name" not in spec:
            result.add_error("name", "Missing required field: name")
        elif len(spec["name"]) > 100:
            result.add_warning("name", "Name should be ≤ 100 characters")
        
        # description (MUST)
        if "description" not in spec:
            result.add_error("description", "Missing required field: description")
        elif len(spec["description"]) > 1000:
            result.add_warning("description", "Description should be ≤ 1000 characters")
    
    def _validate_language(self, spec: Dict, result: ValidationResult):
        """验证语言配置"""
        if "language" not in spec:
            result.add_error("language", "Missing required field: language")
            return
        
        lang = spec["language"]
        if not isinstance(lang, dict):
            result.add_error("language", "language should be an object")
            return
        
        if "name" not in lang:
            result.add_error("language.name", "Missing required: language.name")
    
    def _validate_entrypoint(self, spec: Dict, result: ValidationResult):
        """验证入口点"""
        if "entrypoint" not in spec:
            result.add_error("entrypoint", "Missing required field: entrypoint")
            return
        
        entry = spec["entrypoint"]
        if not isinstance(entry, dict):
            result.add_error("entrypoint", "entrypoint should be an object")
            return
        
        # kind (MUST)
        if "kind" not in entry:
            result.add_error("entrypoint.kind", "Missing required: entrypoint.kind")
        elif entry["kind"] not in self.VALID_ENTRYPOINT_KINDS:
            result.add_error(
                "entrypoint.kind",
                f"Invalid kind: {entry['kind']}",
                f"Should be one of: {self.VALID_ENTRYPOINT_KINDS}"
            )
        else:
            # 根据 kind 验证其他字段
            kind = entry["kind"]
            if kind == "inline" and "code" not in entry:
                result.add_error(
                    "entrypoint.code",
                    "entrypoint.code is required when kind='inline'"
                )
            elif kind == "file" and "path" not in entry:
                result.add_error(
                    "entrypoint.path",
                    "entrypoint.path is required when kind='file'"
                )
        
        # symbol (SHOULD)
        if "symbol" not in entry:
            result.add_warning(
                "entrypoint.symbol",
                "Missing recommended field: entrypoint.symbol",
                "Add the function name/symbol for clarity"
            )
    
    def _validate_signature(self, spec: Dict, result: ValidationResult):
        """验证签名"""
        if "signature" not in spec:
            result.add_error("signature", "Missing required field: signature")
            return
        
        sig = spec["signature"]
        if not isinstance(sig, dict):
            result.add_error("signature", "signature should be an object")
            return
        
        # inputs (MUST)
        if "inputs" not in sig:
            result.add_error("signature.inputs", "Missing required: signature.inputs")
        else:
            inputs = sig["inputs"]
            if not isinstance(inputs, dict):
                result.add_error("signature.inputs", "inputs should be a map (dict)")
            else:
                for name, field_def in inputs.items():
                    self._validate_field_def(f"signature.inputs.{name}", field_def, result)
        
        # outputs (MUST)
        if "outputs" not in sig:
            result.add_error("signature.outputs", "Missing required: signature.outputs")
        else:
            outputs = sig["outputs"]
            if not isinstance(outputs, dict):
                result.add_error("signature.outputs", "outputs should be a map (dict)")
            else:
                for name, field_def in outputs.items():
                    self._validate_field_def(f"signature.outputs.{name}", field_def, result)
    
    def _validate_field_def(self, path: str, field_def: Any, result: ValidationResult):
        """验证字段定义"""
        if not isinstance(field_def, dict):
            result.add_error(path, "Field definition should be an object")
            return
        
        # type (MUST)
        if "type" not in field_def:
            result.add_error(f"{path}.type", "Missing required: type")
        elif field_def["type"] not in self.VALID_TYPES:
            result.add_warning(
                f"{path}.type",
                f"Unknown type: {field_def['type']}",
                f"Should be one of: {self.VALID_TYPES}"
            )
    
    def _validate_semantics(self, spec: Dict, result: ValidationResult):
        """验证语义声明"""
        if "semantics" not in spec:
            result.add_error("semantics", "Missing required field: semantics")
            return
        
        sem = spec["semantics"]
        if not isinstance(sem, dict):
            result.add_error("semantics", "semantics should be an object")
            return
        
        # deterministic (MUST)
        if "deterministic" not in sem:
            result.add_error("semantics.deterministic", "Missing required: semantics.deterministic")
        elif not isinstance(sem["deterministic"], bool):
            result.add_error("semantics.deterministic", "deterministic should be boolean")
        
        # side_effects (MUST)
        if "side_effects" not in sem:
            result.add_error("semantics.side_effects", "Missing required: semantics.side_effects")
        else:
            effects = sem["side_effects"]
            if not isinstance(effects, list):
                result.add_error("semantics.side_effects", "side_effects should be an array")
            else:
                invalid = [e for e in effects if e not in self.VALID_SIDE_EFFECTS]
                if invalid:
                    result.add_warning(
                        "semantics.side_effects",
                        f"Unknown side effects: {invalid}",
                        f"Valid values: {self.VALID_SIDE_EFFECTS}"
                    )
        
        # security (SHOULD)
        if "security" not in sem:
            result.add_warning(
                "semantics.security",
                "Missing recommended field: semantics.security",
                "Add security declaration for agent safety"
            )
    
    def _validate_tests(self, spec: Dict, result: ValidationResult):
        """验证测试"""
        if "tests" not in spec:
            result.add_error("tests", "Missing required field: tests")
            return
        
        tests = spec["tests"]
        if not isinstance(tests, dict):
            result.add_error("tests", "tests should be an object")
            return
        
        # framework (MUST)
        if "framework" not in tests:
            result.add_error("tests.framework", "Missing required: tests.framework")
        
        # cases (MUST, at least 1)
        if "cases" not in tests:
            result.add_error("tests.cases", "Missing required: tests.cases")
        elif not isinstance(tests["cases"], list):
            result.add_error("tests.cases", "tests.cases should be an array")
        elif len(tests["cases"]) == 0:
            result.add_error("tests.cases", "At least one test case is required")
        else:
            for i, case in enumerate(tests["cases"]):
                self._validate_test_case(f"tests.cases[{i}]", case, result)
    
    def _validate_test_case(self, path: str, case: Any, result: ValidationResult):
        """验证单个测试用例"""
        if not isinstance(case, dict):
            result.add_error(path, "Test case should be an object")
            return
        
        if "name" not in case:
            result.add_warning(f"{path}.name", "Test case missing name")
        
        if "input" not in case:
            result.add_error(f"{path}.input", "Test case missing input")
        
        if "expect" not in case:
            result.add_error(f"{path}.expect", "Test case missing expect")
    
    def _validate_optional(self, spec: Dict, result: ValidationResult):
        """验证可选字段"""
        # license (SHOULD)
        if "license" not in spec:
            result.add_warning(
                "license",
                "Missing recommended field: license",
                "Add: license: \"MIT\" (or Apache-2.0, etc.)"
            )
        
        # authors (MAY)
        if "authors" in spec:
            authors = spec["authors"]
            if not isinstance(authors, list):
                result.add_error("authors", "authors should be an array")
        
        # examples (SHOULD)
        if "examples" not in spec:
            result.add_info(
                "examples",
                "Consider adding examples for better documentation"
            )
        
        # provenance (SHOULD)
        if "provenance" not in spec:
            result.add_warning(
                "provenance",
                "Missing recommended field: provenance",
                "Add creation/update timestamps"
            )


def print_result(result: ValidationResult, file_path: Path):
    """打印验证结果"""
    print(f"\n{'='*60}")
    print(f"📋 Validating: {file_path}")
    print('='*60)
    
    if result.valid and len(result.issues) == 0:
        print("✅ All checks passed!")
        return
    
    # 分组显示
    errors = [i for i in result.issues if i.severity == Severity.ERROR]
    warnings = [i for i in result.issues if i.severity == Severity.WARNING]
    infos = [i for i in result.issues if i.severity == Severity.INFO]
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for issue in errors:
            print(f"   [{issue.field}] {issue.message}")
            if issue.suggestion:
                print(f"   💡 {issue.suggestion}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for issue in warnings:
            print(f"   [{issue.field}] {issue.message}")
            if issue.suggestion:
                print(f"   💡 {issue.suggestion}")
    
    if infos:
        print(f"\nℹ️  INFO ({len(infos)}):")
        for issue in infos:
            print(f"   [{issue.field}] {issue.message}")
    
    # 统计
    print(f"\n{'-'*60}")
    print(f"Summary: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} infos")
    print(f"Status: {'✅ VALID' if result.valid else '❌ INVALID'}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate FunctionSpec v0.1 function.yaml files"
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to function directory or function.yaml file"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all functions in examples/ directory"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    
    args = parser.parse_args()
    
    validator = FunctionSpecValidator()
    
    if args.all:
        # 验证所有函数
        examples_dir = Path(__file__).parent.parent / "examples"
        results = []
        
        for func_dir in sorted(examples_dir.iterdir()):
            if not func_dir.is_dir():
                continue
            
            func_file = func_dir / "function.yaml"
            if func_file.exists():
                result = validator.validate_file(func_file)
                results.append({
                    "function": func_dir.name,
                    "valid": result.valid,
                    "stats": result.stats
                })
                
                if not args.json:
                    print_result(result, func_file)
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            # 总统计
            total = len(results)
            valid = sum(1 for r in results if r["valid"])
            print(f"\n{'='*60}")
            print(f"TOTAL: {valid}/{total} functions valid")
    
    elif args.path:
        # 验证单个文件或目录
        path = Path(args.path)
        
        if path.is_dir():
            func_file = path / "function.yaml"
        else:
            func_file = path
        
        result = validator.validate_file(func_file)
        
        if args.strict and any(i.severity == Severity.WARNING for i in result.issues):
            result.valid = False
        
        if args.json:
            output = {
                "valid": result.valid,
                "stats": result.stats,
                "issues": [
                    {
                        "severity": i.severity.value,
                        "field": i.field,
                        "message": i.message,
                        "suggestion": i.suggestion
                    }
                    for i in result.issues
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            print_result(result, func_file)
        
        sys.exit(0 if result.valid else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
