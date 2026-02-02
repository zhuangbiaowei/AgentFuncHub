#!/usr/bin/env python3
"""
数据迁移脚本: function.yaml → PostgreSQL

用法:
    python scripts/migrate_to_postgres.py
    python scripts/migrate_to_postgres.py --reset  # 重置数据库
"""

import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# 添加 src/server 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "server"))

from database import init_db, reset_db, get_db
from database.models import Function


def parse_datetime(date_str: str) -> datetime:
    """解析 ISO 格式日期"""
    if not date_str:
        return None
    try:
        # 处理带 Z 的格式
        date_str = date_str.replace('Z', '+00:00')
        return datetime.fromisoformat(date_str)
    except:
        return None


def extract_search_text(spec: dict) -> str:
    """提取用于全文搜索的文本"""
    parts = [
        spec.get("name", ""),
        spec.get("description", ""),
        spec.get("id", "")
    ]
    
    # 添加标签
    tags = spec.get("tags", [])
    parts.extend(tags)
    
    # 从 signature 提取参数名
    signature = spec.get("signature", {})
    inputs = signature.get("inputs", {})
    outputs = signature.get("outputs", {})
    
    for param_name in inputs.keys():
        parts.append(param_name)
    for param_name in outputs.keys():
        parts.append(param_name)
    
    # 过滤空值并连接
    return " ".join(filter(None, parts))


def migrate_function(yaml_path: Path, db) -> bool:
    """迁移单个函数"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)
        
        if not spec:
            print(f"⚠️  Empty spec: {yaml_path}")
            return False
        
        spec_id = spec.get("id")
        if not spec_id:
            print(f"⚠️  Missing id in: {yaml_path}")
            return False
        
        # 检查是否已存在
        existing = db.query(Function).filter(Function.spec_id == spec_id).first()
        if existing:
            print(f"⏭️  Skipping (exists): {spec_id}")
            return False
        
        # 提取语言信息
        language = spec.get("language", {})
        lang_name = language.get("name", "python")
        lang_runtime = language.get("runtime")
        
        # 提取入口点信息
        entrypoint = spec.get("entrypoint", {})
        entrypoint_kind = entrypoint.get("kind", "inline")
        entrypoint_symbol = entrypoint.get("symbol", "")
        entrypoint_code = entrypoint.get("code")
        
        # 提取签名信息
        signature = spec.get("signature", {})
        signature_inputs = signature.get("inputs", {})
        signature_outputs = signature.get("outputs", {})
        
        # 提取语义信息
        semantics = spec.get("semantics", {})
        semantics_deterministic = semantics.get("deterministic", True)
        semantics_side_effects = semantics.get("side_effects", ["none"])
        semantics_purity = semantics.get("purity", "pure")
        semantics_security = semantics.get("security", {})
        
        # 提取标签
        tags = spec.get("tags", [])
        
        # 生成搜索文本
        search_text_content = extract_search_text(spec)
        
        # 提取质量信息
        quality = spec.get("quality", {})
        quality_maturity = quality.get("maturity", "experimental")
        quality_coverage = quality.get("coverage", 0.0)
        
        # 提取溯源信息
        provenance = spec.get("provenance", {})
        provenance_created_at = parse_datetime(provenance.get("created_at"))
        provenance_updated_at = parse_datetime(provenance.get("updated_at"))
        provenance_source_kind = provenance.get("source", {}).get("kind", "manual")
        
        # 创建 Function 记录
        func = Function(
            spec_id=spec_id,
            name=spec.get("name", ""),
            description=spec.get("description", ""),
            version=spec.get("version", "1.0.0"),
            language=lang_name,
            runtime=lang_runtime,
            spec_json=spec,
            entrypoint_kind=entrypoint_kind,
            entrypoint_symbol=entrypoint_symbol,
            entrypoint_code=entrypoint_code,
            signature_inputs=signature_inputs,
            signature_outputs=signature_outputs,
            semantics_deterministic=semantics_deterministic,
            semantics_side_effects=semantics_side_effects,
            semantics_purity=semantics_purity,
            semantics_security=semantics_security,
            tags=tags,
            # search_text 需要在数据库中生成
            quality_maturity=quality_maturity,
            quality_coverage=quality_coverage,
            license=spec.get("license", "MIT"),
            provenance_created_at=provenance_created_at,
            provenance_updated_at=provenance_updated_at,
            provenance_source_kind=provenance_source_kind,
            is_public=True,
            is_deprecated=False
        )
        
        db.add(func)
        print(f"✅ Migrated: {spec_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating {yaml_path}: {e}")
        return False


def migrate_all(examples_dir: Path, db) -> tuple[int, int]:
    """迁移所有函数"""
    migrated = 0
    skipped = 0
    
    for func_dir in sorted(examples_dir.iterdir()):
        if func_dir.is_dir():
            yaml_path = func_dir / "function.yaml"
            if yaml_path.exists():
                if migrate_function(yaml_path, db):
                    migrated += 1
                else:
                    skipped += 1
    
    return migrated, skipped


def update_search_text(db):
    """更新所有函数的 search_text (使用数据库的 to_tsvector)"""
    try:
        from sqlalchemy import text
        
        # 使用 PL/pgSQL 更新 search_text
        db.execute(text("""
            UPDATE functions
            SET search_text = to_tsvector('chinese', 
                COALESCE(name, '') || ' ' ||
                COALESCE(description, '') || ' ' ||
                COALESCE(array_to_string(tags, ' '), '') || ' ' ||
                COALESCE(spec_id, '')
            )
            WHERE search_text IS NULL;
        """))
        db.commit()
        print("✅ Search text updated")
    except Exception as e:
        print(f"⚠️  Could not update search text: {e}")


def main():
    parser = argparse.ArgumentParser(description="Migrate functions from YAML to PostgreSQL")
    parser.add_argument("--reset", action="store_true", help="Reset database before migration")
    parser.add_argument("--examples-dir", type=str, default="examples", help="Examples directory")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 AgentFuncHub Data Migration")
    print("=" * 60)
    
    # 初始化数据库
    if args.reset:
        print("\n🔄 Resetting database...")
        reset_db()
    else:
        print("\n🔄 Initializing database...")
        init_db()
    
    # 查找 examples 目录
    examples_dir = Path(__file__).parent.parent / args.examples_dir
    if not examples_dir.exists():
        print(f"❌ Examples directory not found: {examples_dir}")
        sys.exit(1)
    
    print(f"\n📁 Examples directory: {examples_dir}")
    
    # 执行迁移
    with get_db() as db:
        print("\n🔄 Migrating functions...")
        migrated, skipped = migrate_all(examples_dir, db)
        
        # 更新 search_text
        print("\n🔄 Updating search vectors...")
        update_search_text(db)
    
    print("\n" + "=" * 60)
    print(f"📊 Migration complete: {migrated} migrated, {skipped} skipped")
    print("=" * 60)


if __name__ == "__main__":
    main()
