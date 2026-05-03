#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例数据填充脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from core.database import init_database
from core.config import load_config
from shared.models import (
    User, Category, Product, Supplier, 
    PurchaseOrder, PurchaseItem, SaleOrder, SaleItem
)
import random
import datetime
import hashlib

# 生成密码哈希
def generate_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 生成订单号
def generate_order_no(prefix):
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_num = random.randint(1000, 9999)
    return f"{prefix}{timestamp}{random_num}"

# 填充用户数据
def fill_users(session):
    users = [
        {
            'username': 'admin',
            'password_hash': generate_password_hash('admin123'),
            'role': '管理员',
            'real_name': '管理员',
            'status': '正常'
        },
        {
            'username': 'cashier1',
            'password_hash': generate_password_hash('cashier123'),
            'role': '收银员',
            'real_name': '收银员1',
            'status': '正常'
        },
        {
            'username': 'manager',
            'password_hash': generate_password_hash('manager123'),
            'role': '经理',
            'real_name': '经理',
            'status': '正常'
        }
    ]
    
    for user_data in users:
        existing_user = session.query(User).filter_by(username=user_data['username']).first()
        if not existing_user:
            user = User(**user_data)
            session.add(user)
    
    session.commit()
    print("用户数据填充完成")

# 填充分类数据
def fill_categories(session):
    categories_data = [
        {'name': '食品饮料', 'parent_id': None, 'description': '各类食品和饮料'},
        {'name': '休闲零食', 'parent_id': 1, 'description': '各种休闲零食'},
        {'name': '饮料', 'parent_id': 1, 'description': '各种饮料'},
        {'name': '日用品', 'parent_id': None, 'description': '日常生活用品'},
        {'name': '洗漱用品', 'parent_id': 4, 'description': '洗漱相关用品'},
        {'name': '清洁用品', 'parent_id': 4, 'description': '清洁相关用品'},
        {'name': '电子产品', 'parent_id': None, 'description': '各类电子产品'},
        {'name': '手机配件', 'parent_id': 7, 'description': '手机相关配件'},
        {'name': '电脑配件', 'parent_id': 7, 'description': '电脑相关配件'}
    ]
    
    for cat_data in categories_data:
        existing_cat = session.query(Category).filter_by(name=cat_data['name']).first()
        if not existing_cat:
            category = Category(**cat_data)
            session.add(category)
    
    session.commit()
    print("分类数据填充完成")

# 填充供应商数据
def fill_suppliers(session):
    suppliers_data = [
        {
            'code': 'SP001',
            'name': '食品供应商',
            'contact': '张三',
            'phone': '13800138001',
            'address': '北京市朝阳区食品街1号',
            'remark': '主要供应食品和饮料'
        },
        {
            'code': 'SP002',
            'name': '日用品供应商',
            'contact': '李四',
            'phone': '13800138002',
            'address': '北京市海淀区日用品市场2号',
            'remark': '主要供应日用品'
        },
        {
            'code': 'SP003',
            'name': '电子产品供应商',
            'contact': '王五',
            'phone': '13800138003',
            'address': '北京市西城区电子市场3号',
            'remark': '主要供应电子产品'
        }
    ]
    
    for supplier_data in suppliers_data:
        existing_supplier = session.query(Supplier).filter_by(code=supplier_data['code']).first()
        if not existing_supplier:
            supplier = Supplier(**supplier_data)
            session.add(supplier)
    
    session.commit()
    print("供应商数据填充完成")

# 填充商品数据
def fill_products(session):
    # 获取所有分类
    categories = session.query(Category).all()
    category_map = {cat.id: cat for cat in categories}
    
    products_data = [
        # 食品饮料类
        {
            'code': 'P001',
            'barcode': '6901234567890',
            'name': '可口可乐',
            'category_id': 3,  # 饮料
            'brand': '可口可乐',
            'specification': '330ml',
            'price_cost': 2.0,
            'price_sale': 3.0,
            'price_member': 2.8,
            'stock_quantity': 100.0,
            'min_stock': 10.0,
            'max_stock': 200.0,
            'status': '正常',
            'description': '可口可乐碳酸饮料'
        },
        {
            'code': 'P002',
            'barcode': '6901234567891',
            'name': '百事可乐',
            'category_id': 3,  # 饮料
            'brand': '百事可乐',
            'specification': '330ml',
            'price_cost': 1.9,
            'price_sale': 3.0,
            'price_member': 2.8,
            'stock_quantity': 90.0,
            'min_stock': 10.0,
            'max_stock': 200.0,
            'status': '正常',
            'description': '百事可乐碳酸饮料'
        },
        {
            'code': 'P003',
            'barcode': '6901234567892',
            'name': '薯片',
            'category_id': 2,  # 休闲零食
            'brand': '乐事',
            'specification': '45g',
            'price_cost': 2.5,
            'price_sale': 4.0,
            'price_member': 3.8,
            'stock_quantity': 80.0,
            'min_stock': 10.0,
            'max_stock': 150.0,
            'status': '正常',
            'description': '乐事薯片'
        },
        # 日用品类
        {
            'code': 'P004',
            'barcode': '6901234567893',
            'name': '牙刷',
            'category_id': 5,  # 洗漱用品
            'brand': '高露洁',
            'specification': '单支',
            'price_cost': 1.5,
            'price_sale': 3.0,
            'price_member': 2.8,
            'stock_quantity': 120.0,
            'min_stock': 20.0,
            'max_stock': 200.0,
            'status': '正常',
            'description': '高露洁牙刷'
        },
        {
            'code': 'P005',
            'barcode': '6901234567894',
            'name': '牙膏',
            'category_id': 5,  # 洗漱用品
            'brand': '佳洁士',
            'specification': '120g',
            'price_cost': 5.0,
            'price_sale': 9.0,
            'price_member': 8.5,
            'stock_quantity': 60.0,
            'min_stock': 10.0,
            'max_stock': 100.0,
            'status': '正常',
            'description': '佳洁士牙膏'
        },
        # 电子产品类
        {
            'code': 'P006',
            'barcode': '6901234567895',
            'name': '手机充电器',
            'category_id': 8,  # 手机配件
            'brand': '华为',
            'specification': '20W',
            'price_cost': 20.0,
            'price_sale': 39.9,
            'price_member': 38.0,
            'stock_quantity': 30.0,
            'min_stock': 5.0,
            'max_stock': 50.0,
            'status': '正常',
            'description': '华为手机充电器'
        },
        {
            'code': 'P007',
            'barcode': '6901234567896',
            'name': 'USB数据线',
            'category_id': 8,  # 手机配件
            'brand': '小米',
            'specification': '1m',
            'price_cost': 8.0,
            'price_sale': 19.9,
            'price_member': 18.0,
            'stock_quantity': 50.0,
            'min_stock': 10.0,
            'max_stock': 100.0,
            'status': '正常',
            'description': '小米USB数据线'
        }
    ]
    
    for product_data in products_data:
        existing_product = session.query(Product).filter_by(code=product_data['code']).first()
        if not existing_product:
            product = Product(**product_data)
            session.add(product)
    
    session.commit()
    print("商品数据填充完成")

# 填充采购订单数据
def fill_purchase_orders(session):
    # 获取所有供应商和商品
    suppliers = session.query(Supplier).all()
    products = session.query(Product).all()
    
    # 生成10个采购订单
    for i in range(10):
        supplier = random.choice(suppliers)
        order_no = generate_order_no('PO')
        
        # 随机选择3-5个商品作为采购明细
        order_products = random.sample(products, random.randint(3, 5))
        total_amount = 0.0
        
        purchase_order = PurchaseOrder(
            order_no=order_no,
            supplier_id=supplier.id,
            total_amount=0.0,  # 稍后计算
            status=random.choice(['已完成', '待入库']),
            remark=f'采购订单{i+1}'
        )
        session.add(purchase_order)
        session.flush()  # 获取订单ID
        
        # 创建采购明细
        for product in order_products:
            quantity = random.randint(10, 50)
            price = product.price_cost
            amount = quantity * price
            total_amount += amount
            
            purchase_item = PurchaseItem(
                purchase_id=purchase_order.id,
                product_id=product.id,
                quantity=quantity,
                price=price,
                amount=amount
            )
            session.add(purchase_item)
        
        # 更新订单总金额
        purchase_order.total_amount = total_amount
        
        # 如果订单状态为已完成，设置完成时间
        if purchase_order.status == '已完成':
            purchase_order.finish_time = datetime.datetime.now()
    
    session.commit()
    print("采购订单数据填充完成")

# 填充销售订单数据
def fill_sale_orders(session):
    # 获取所有商品
    products = session.query(Product).all()
    
    # 支付方式
    payment_methods = ['现金', '微信', '支付宝', '银行卡']
    
    # 生成20个销售订单
    for i in range(20):
        order_no = generate_order_no('SO')
        
        # 随机选择1-5个商品作为销售明细
        order_products = random.sample(products, random.randint(1, 5))
        total_amount = 0.0
        discount_amount = 0.0
        
        sale_order = SaleOrder(
            order_no=order_no,
            total_amount=0.0,  # 稍后计算
            discount_amount=discount_amount,
            actual_amount=0.0,  # 稍后计算
            payment_method=random.choice(payment_methods),
            status='已完成',
            operator=random.choice(['admin', 'cashier1']),
            remark=f'销售订单{i+1}'
        )
        session.add(sale_order)
        session.flush()  # 获取订单ID
        
        # 创建销售明细
        for product in order_products:
            quantity = random.randint(1, 5)
            price = product.price_sale
            amount = quantity * price
            total_amount += amount
            
            sale_item = SaleItem(
                sale_id=sale_order.id,
                product_id=product.id,
                quantity=quantity,
                price=price,
                amount=amount
            )
            session.add(sale_item)
        
        # 随机生成折扣
        if random.random() > 0.7:  # 30%的概率有折扣
            discount_amount = round(total_amount * random.uniform(0.05, 0.1), 2)
        
        actual_amount = total_amount - discount_amount
        
        # 更新订单金额
        sale_order.total_amount = total_amount
        sale_order.discount_amount = discount_amount
        sale_order.actual_amount = actual_amount
    
    session.commit()
    print("销售订单数据填充完成")

# 主函数
def main():
    print("开始填充示例数据...")
    
    # 初始化数据库
    try:
        config = load_config()
        init_database(config.get('database', {}))
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return
    
    # 初始化数据库后，导入 db_session
    from core.database import db_session
    
    try:
        with db_session() as session:
            print("\n1. 填充用户数据...")
            fill_users(session)
            
            print("\n2. 填充分类数据...")
            fill_categories(session)
            
            print("\n3. 填充供应商数据...")
            fill_suppliers(session)
            
            print("\n4. 填充商品数据...")
            fill_products(session)
            
            print("\n5. 填充采购订单数据...")
            fill_purchase_orders(session)
            
            print("\n6. 填充销售订单数据...")
            fill_sale_orders(session)
        
        print("\n示例数据填充完成！")
        print("\n默认用户:")
        print("  管理员: admin / admin123")
        print("  收银员: cashier1 / cashier123")
        print("  经理: manager / manager123")
        
    except Exception as e:
        print(f"填充数据时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
