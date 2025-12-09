import re
import sqlparse
from app.core.config import settings

FORBIDDEN = re.compile(r"\\b(drop|delete|update|insert|alter|create|truncate|grant|revoke)\\b", re.I)

def is_safe_sql(sql: str) -> bool:
    if not sql:
        return False
    if FORBIDDEN.search(sql):
        return False
    parsed = sqlparse.parse(sql)
    if len(parsed) != 1:
        return False
    stmt = parsed[0]
    if stmt.get_type() != 'SELECT':
        return False
    # crude LIMIT guard
    if "limit" not in sql.lower():
        return False
    return True

def clamp_limit(sql: str) -> str:
    # best-effort: if LIMIT > MAX_LIMIT, clamp it
    m = re.search(r"limit\\s+(\\d+)", sql, flags=re.I)
    if m:
        n = int(m.group(1))
        if n > settings.MAX_LIMIT:
            return re.sub(r"limit\\s+\\d+", f"LIMIT {settings.MAX_LIMIT}", sql, flags=re.I)
        return sql
    return f"{sql.rstrip(';')} LIMIT {settings.MAX_LIMIT};"
  