"""
数据库初始化和管理
"""
import sqlite3
import os

DB_PATH = 'data/database.db'


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _safe_add_column(cursor, table, column, col_type):
    """安全地向已有表添加列（列已存在则跳过）"""
    try:
        cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}')
    except sqlite3.OperationalError:
        pass


def init_db():
    """初始化数据库表"""
    os.makedirs('data', exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    # ── 用户表 ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── 群组表 ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            grpkey_path TEXT,
            mgrkey_path TEXT,
            gml_path TEXT
        )
    ''')

    # ── 成员表 ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            group_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            memkey_path TEXT,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ── 签名表 ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            member_id INTEGER,
            message TEXT NOT NULL,
            signature_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT 0,
            opened BOOLEAN DEFAULT 0,
            signer_index INTEGER,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    ''')

    # ── 操作日志表（审计） ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ── 涉密文件表 ──
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            doc_number TEXT,
            content TEXT,
            classification_level TEXT DEFAULT '秘密',
            status TEXT DEFAULT 'pending',
            group_id INTEGER NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # ── 安全地为已有表添加新列（数据库迁移兼容） ──
    new_columns = [
        ('groups', 'description', 'TEXT'),
        ('groups', 'classification_level', "TEXT DEFAULT '秘密'"),
        ('groups', 'created_by', 'INTEGER'),
        ('members', 'gml_index', 'INTEGER'),
        ('members', 'status', "TEXT DEFAULT 'active'"),
        ('signatures', 'document_id', 'INTEGER'),
        ('signatures', 'signer_name', 'TEXT'),
        ('users', 'display_name', 'TEXT'),
        ('users', 'department', 'TEXT'),
    ]
    for table, column, col_type in new_columns:
        _safe_add_column(cursor, table, column, col_type)

    conn.commit()
    conn.close()
