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
    return conn

def init_db():
    """初始化数据库表"""
    os.makedirs('data', exist_ok=True)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 群组表
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
    
    # 成员表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            memkey_path TEXT,
            FOREIGN KEY (group_id) REFERENCES groups(id)
        )
    ''')
    
    # 签名表
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
    
    conn.commit()
    conn.close()
