import sqlite3
import os

# 连接到数据库
db_path = os.path.join('backend', 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询用户数据
cursor.execute('SELECT id, username, department, real_name FROM users')
rows = cursor.fetchall()

print('用户数据:')
for row in rows:
    print(f'ID: {row[0]}, 用户名: {row[1]}, 部门: {row[2]}, 真实姓名: {row[3]}')

conn.close() 