from datetime import datetime
import random

def generate_order_no(prefix='SO'):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    return f'{prefix}{timestamp}{random_suffix}'

def generate_purchase_order_no():
    return generate_order_no('PO')

def generate_sale_order_no():
    return generate_order_no('SO')

def generate_member_no():
    return 'M' + datetime.now().strftime('%Y%m%d') + ''.join([str(random.randint(0, 9)) for _ in range(4)])

def generate_product_code():
    return 'P' + datetime.now().strftime('%Y%m%d%H%M') + ''.join([str(random.randint(0, 9)) for _ in range(3)])

def generate_supplier_code():
    return 'S' + datetime.now().strftime('%Y%m%d') + ''.join([str(random.randint(0, 9)) for _ in range(4)])
