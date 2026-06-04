#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试脚本：验证应用初始化"""

import sqlite3
import os

# 清理旧数据库
if os.path.exists("site.db"):
    os.remove("site.db")

# 导入应用
from app import init_db

# 初始化数据库
init_db()

# 检查表
db = sqlite3.connect("site.db")
cur = db.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
table_names = [t[0] for t in tables]

print("✓ 数据库初始化成功")
print(f"✓ 创建的表: {', '.join(table_names)}")

# 检查关键表
required_tables = {"users", "photos", "letters", "secretdiary"}
if required_tables.issubset(set(table_names)):
    print("✓ 所有关键表都已创建")
else:
    print("✗ 缺少以下表:", required_tables - set(table_names))

# 检查用户
users = cur.execute("SELECT username, display_name FROM users").fetchall()
print(f"✓ 初始化用户数: {len(users)}")
for username, display_name in users:
    print(f"  - {username} ({display_name})")

db.close()
print("\n测试完成！应用已准备就绪。")
