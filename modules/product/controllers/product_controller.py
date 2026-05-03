from sqlalchemy.orm import Session
from shared.models.product import Product, Category
from shared.utils.order_generator import generate_product_code
from core.logger import logger
from core.event_bus import publish_event

class ProductController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_product(self, **kwargs):
        if 'code' not in kwargs or not kwargs['code']:
            kwargs['code'] = generate_product_code()
        
        product = Product(**kwargs)
        self.db.add(product)
        self.db.commit()
        
        logger.info(f"创建商品: {product.code} - {product.name}")
        publish_event('product_created', product_id=product.id)
        
        return product
    
    def get_product(self, product_id):
        return self.db.get(Product, product_id)
    
    def get_product_by_code(self, code):
        return self.db.query(Product).filter(Product.code == code).first()
    
    def get_product_by_barcode(self, barcode):
        return self.db.query(Product).filter(Product.barcode == barcode).first()
    
    def list_products(self, category_id=None, status=None, keyword=None):
        query = self.db.query(Product)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if status:
            query = query.filter(Product.status == status)
        if keyword:
            query = query.filter(
                (Product.name.contains(keyword)) | 
                (Product.code.contains(keyword)) |
                (Product.barcode.contains(keyword))
            )
        
        return query.order_by(Product.create_time.desc()).all()
    
    def update_product(self, product_id, **kwargs):
        product = self.get_product(product_id)
        if not product:
            return None
        
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        self.db.commit()
        logger.info(f"更新商品: {product.code} - {product.name}")
        publish_event('product_updated', product_id=product.id)
        
        return product
    
    def delete_product(self, product_id):
        product = self.get_product(product_id)
        if not product:
            return False
        
        product.status = '已停用'
        self.db.commit()
        logger.info(f"停用商品: {product.code} - {product.name}")
        publish_event('product_deleted', product_id=product.id)
        
        return True
    
    def get_low_stock_products(self):
        return self.db.query(Product).filter(
            Product.stock_quantity <= Product.min_stock,
            Product.status == '正常'
        ).all()
    
    def create_category(self, **kwargs):
        category = Category(**kwargs)
        self.db.add(category)
        self.db.commit()
        return category
    
    def get_category_by_name(self, name):
        return self.db.query(Category).filter(Category.name == name).first()
    
    def get_categories(self, parent_id=None):
        query = self.db.query(Category)
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        return query.order_by(Category.name).all()
    
    def get_category(self, category_id):
        return self.db.get(Category, category_id)
    
    def update_category(self, category_id, **kwargs):
        category = self.get_category(category_id)
        if not category:
            return None
        
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        
        self.db.commit()
        return category
    
    def delete_category(self, category_id):
        category = self.get_category(category_id)
        if not category:
            return False
        
        children = self.get_categories(parent_id=category_id)
        if children:
            for child in children:
                child.parent_id = category.parent_id
            
            products = self.list_products(category_id=category_id)
            for product in products:
                product.category_id = category.parent_id
        
        self.db.delete(category)
        self.db.commit()
        return True
