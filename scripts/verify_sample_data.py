#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证示例数据填充脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_database
from core.config import load_config

# 主函数
def main():
    print("开始验证示例数据...")
    
    # 初始化数据库
    try:
        config = load_config()
        init_database(config.get('database', {}))
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return
    
    # 初始化数据库后，导入 db_session 和模型
    from core.database import db_session
    from shared.models import (
        User, Category, Product, Supplier, 
        PurchaseOrder, PurchaseItem, SaleOrder, SaleItem
    )
    
    try:
        with db_session() as session:
            # 验证用户数据
            print("\n1. 验证用户数据...")
            users = session.query(User).all()
            print(f"用户数量: {len(users)}")
            for user in users:
                print(f"  - {user.username} ({user.role})")
            
            # 验证分类数据
            print("\n2. 验证分类数据...")
            categories = session.query(Category).all()
            print(f"分类数量: {len(categories)}")
            for category in categories:
                parent_name = category.parent.name if category.parent else "无"
                print(f"  - {category.name} (父分类: {parent_name})")
            
            # 验证供应商数据
            print("\n3. 验证供应商数据...")
            suppliers = session.query(Supplier).all()
            print(f"供应商数量: {len(suppliers)}")
            for supplier in suppliers:
                print(f"  - {supplier.name} ({supplier.code})")
            
            # 验证商品数据
            print("\n4. 验证商品数据...")
            products = session.query(Product).all()
            print(f"商品数量: {len(products)}")
            for product in products[:5]:  # 只显示前5个商品
                category_name = product.category.name if product.category else "无"
                print(f"  - {product.name} ({product.code}) - 分类: {category_name}")
            if len(products) > 5:
                print(f"  ... 还有 {len(products) - 5} 个商品")
            
            # 验证采购订单数据
            print("\n5. 验证采购订单数据...")
            purchase_orders = session.query(PurchaseOrder).all()
            print(f"采购订单数量: {len(purchase_orders)}")
            for order in purchase_orders[:3]:  # 只显示前3个订单
                supplier_name = order.supplier.name if order.supplier else "无"
                item_count = len(order.items)
                print(f"  - {order.order_no} - 供应商: {supplier_name} - 明细: {item_count} 项")
            if len(purchase_orders) > 3:
                print(f"  ... 还有 {len(purchase_orders) - 3} 个采购订单")
            
            # 验证销售订单数据
            print("\n6. 验证销售订单数据...")
            sale_orders = session.query(SaleOrder).all()
            print(f"销售订单数量: {len(sale_orders)}")
            for order in sale_orders[:3]:  # 只显示前3个订单
                item_count = len(order.items)
                print(f"  - {order.order_no} - 支付方式: {order.payment_method} - 明细: {item_count} 项")
            if len(sale_orders) > 3:
                print(f"  ... 还有 {len(sale_orders) - 3} 个销售订单")
        
        print("\n示例数据验证完成！")
        
    except Exception as e:
        print(f"验证数据时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
