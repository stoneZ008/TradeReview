# A股行业分类数据库

import sqlite3
import json
from datetime import datetime
import os
from db_migrate import ensure_columns

# 数据库文件路径
DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))
DB_PATH = os.path.join(DATA_DIR, 'industries.db')

INDUSTRY_SCHEMA_COLUMNS = {
    'industries': [
        ('name', 'TEXT NOT NULL'),
        ('icon', "TEXT NOT NULL DEFAULT '🏢'"),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ],
    'sub_industries': [
        ('industry_id', 'INTEGER NOT NULL'),
        ('name', 'TEXT NOT NULL'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ],
    'companies': [
        ('sub_industry_id', 'INTEGER NOT NULL'),
        ('code', 'TEXT NOT NULL'),
        ('name', 'TEXT NOT NULL'),
        ('role', 'TEXT'),
        ('feature', 'TEXT'),
        ('description', 'TEXT'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ],
}

def init_db():
    """初始化数据库表"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建行业表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS industries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '🏢',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建子行业表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sub_industries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (industry_id) REFERENCES industries(id) ON DELETE CASCADE
        )
    ''')
    
    # 创建公司表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_industry_id INTEGER NOT NULL,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            role TEXT,
            feature TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sub_industry_id) REFERENCES sub_industries(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def migrate_industry_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    for table_name, columns in INDUSTRY_SCHEMA_COLUMNS.items():
        ensure_columns(conn, table_name, columns)
    conn.close()

def seed_default_data():
    """初始化默认数据"""
    init_db()
    migrate_industry_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute('SELECT COUNT(*) FROM industries')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # 插入默认行业数据
    industries = [
        ('光模块', '📡'),
        ('芯片', '💾'),
        ('服务器/算力', '🖥️'),
        ('新能源', '⚡')
    ]
    
    for name, icon in industries:
        cursor.execute('INSERT INTO industries (name, icon) VALUES (?, ?)', (name, icon))
    
    # 获取行业ID
    cursor.execute('SELECT id, name FROM industries')
    industry_map = {name: id for id, name in cursor.fetchall()}
    
    # 插入子行业数据
    sub_industries = [
        (industry_map['光模块'], 'EML芯片'),
        (industry_map['光模块'], 'CPO（共封装光学）'),
        (industry_map['光模块'], '硅光'),
        (industry_map['芯片'], 'GPU/AI芯片'),
        (industry_map['芯片'], '存储芯片'),
        (industry_map['服务器/算力'], 'AI服务器'),
        (industry_map['新能源'], '光伏')
    ]
    
    for industry_id, name in sub_industries:
        cursor.execute('INSERT INTO sub_industries (industry_id, name) VALUES (?, ?)', (industry_id, name))
    
    # 获取子行业ID
    cursor.execute('SELECT id, name FROM sub_industries')
    sub_industry_map = {name: id for id, name in cursor.fetchall()}
    
    # 插入公司数据
    companies = [
        (sub_industry_map['EML芯片'], '300394', '天孚通信', '光模块龙头', '800G/1.6T高速光模块量产能力，绑定头部客户', '光模块产品研发制造'),
        (sub_industry_map['EML芯片'], '300502', '新易盛', '800G光模块', '800G硅光模块领先，海外大客户突破', '高速光模块供应商'),
        (sub_industry_map['EML芯片'], '603083', '剑桥科技', '光模块', '5G前传光模块，海外业务占比高', '光通信产品'),
        (sub_industry_map['CPO（共封装光学）'], '002281', '光迅科技', 'CPO龙头', '国内光器件龙头，CPO方案储备充分', '光通信器件'),
        (sub_industry_map['CPO（共封装光学）'], '300570', '太辰光', 'CPO', '光无源器件，CPO封装布局', '光无源器件'),
        (sub_industry_map['硅光'], '688800', '源杰科技', '硅光芯片', '硅光芯片国产替代，25G/50G产品量产', '光芯片'),
        (sub_industry_map['GPU/AI芯片'], '688041', '海光信息', '国产GPU龙头', '深海系列GPU，国产AI算力核心', '国产GPU研发'),
        (sub_industry_map['GPU/AI芯片'], '688256', '寒武纪', 'AI芯片', '思元系列AI芯片，大模型训练推理', 'AI芯片设计'),
        (sub_industry_map['存储芯片'], '002049', '紫光国微', '存储芯片', '国产存储芯片龙头，DRAM+NAND布局', '存储芯片设计'),
        (sub_industry_map['AI服务器'], '000977', '浪潮信息', 'AI服务器龙头', '国内AI服务器市占率第一，深度绑定英伟达', '服务器研发制造'),
        (sub_industry_map['AI服务器'], '603019', '中科曙光', '算力', '国产算力基础设施，海光生态', '高性能计算'),
        (sub_industry_map['光伏'], '300750', '宁德时代', '动力电池龙头', '全球动力电池市占率第一', '动力电池研发制造')
    ]
    
    for company in companies:
        cursor.execute('''
            INSERT INTO companies (sub_industry_id, code, name, role, feature, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', company)
    
    conn.commit()
    conn.close()
    print('默认数据初始化完成')

def get_all_industries():
    """获取所有行业数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有行业
    cursor.execute('''
        SELECT id, name, icon FROM industries ORDER BY id
    ''')
    industries = [dict(row) for row in cursor.fetchall()]
    
    # 获取所有子行业
    cursor.execute('''
        SELECT id, industry_id, name FROM sub_industries ORDER BY id
    ''')
    sub_industries = [dict(row) for row in cursor.fetchall()]
    
    # 获取所有公司
    cursor.execute('''
        SELECT id, sub_industry_id, code, name, role, feature, description
        FROM companies
        ORDER BY id
    ''')
    companies = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # 组装数据结构
    result = []
    for industry in industries:
        children = []
        for sub in sub_industries:
            if sub['industry_id'] == industry['id']:
                sub_companies = [
                    {
                        'id': c['id'],
                        'code': c['code'],
                        'name': c['name'],
                        'role': c['role'],
                        'feature': c['feature'],
                        'desc': c['description']
                    }
                    for c in companies
                    if c['sub_industry_id'] == sub['id']
                ]
                children.append({
                    'id': str(sub['id']),
                    'name': sub['name'],
                    'companies': sub_companies
                })
        
        result.append({
            'id': str(industry['id']),
            'name': industry['name'],
            'icon': industry['icon'],
            'children': children
        })
    
    return result

def add_industry(name, icon='🏢'):
    """添加行业"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO industries (name, icon) VALUES (?, ?)', (name, icon))
    industry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return industry_id

def update_industry(industry_id, name, icon):
    """更新行业"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE industries SET name=?, icon=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', 
                   (name, icon, industry_id))
    conn.commit()
    conn.close()

def add_sub_industry(industry_id, name):
    """添加子行业"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sub_industries (industry_id, name) VALUES (?, ?)', (industry_id, name))
    sub_industry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sub_industry_id

def update_sub_industry(sub_industry_id, name):
    """更新子行业"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE sub_industries SET name=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', 
                   (name, sub_industry_id))
    conn.commit()
    conn.close()

def add_company(sub_industry_id, code, name, role, feature, desc):
    """添加公司"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO companies (sub_industry_id, code, name, role, feature, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (sub_industry_id, code, name, role, feature, desc))
    company_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return company_id

def update_company(company_id, code, name, role, feature, desc):
    """更新公司"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE companies 
        SET code=?, name=?, role=?, feature=?, description=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (code, name, role, feature, desc, company_id))
    conn.commit()
    conn.close()

def delete_company(company_id):
    """删除公司"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM companies WHERE id=?', (company_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed_default_data()
