"""ORM tanımlarından PostgreSQL DDL'ini yazdırır; backend/db/schema.sql ile karşılaştırma için.
Kullanım: python backend/db/print_ddl.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.schema import CreateTable  # noqa: E402
from backend.app.db import Base  # noqa: E402

for table in Base.metadata.sorted_tables:
    print(str(CreateTable(table).compile(dialect=postgresql.dialect())).strip() + ";\n")
