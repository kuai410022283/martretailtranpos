import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mrtpos.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 检查并更新 purchase_orders 表
        cursor.execute("PRAGMA table_info(purchase_orders)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'order_type' not in columns:
            print("添加 order_type 列到 purchase_orders 表...")
            cursor.execute("ALTER TABLE purchase_orders ADD COLUMN order_type VARCHAR(20) DEFAULT '采购'")
        
        if 'ref_order_no' not in columns:
            print("添加 ref_order_no 列到 purchase_orders 表...")
            cursor.execute("ALTER TABLE purchase_orders ADD COLUMN ref_order_no VARCHAR(20)")
            
        # 2. 检查并更新 stock_logs 表
        cursor.execute("PRAGMA table_info(stock_logs)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'cost_price' not in columns:
            print("添加 cost_price 列到 stock_logs 表...")
            cursor.execute("ALTER TABLE stock_logs ADD COLUMN cost_price FLOAT")
            
        conn.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
