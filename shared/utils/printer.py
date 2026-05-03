from core.logger import logger

class Printer:
    def __init__(self, printer_name=None):
        self.printer_name = printer_name
    
    def print_text(self, text):
        logger.info(f"打印文本: {text}")
        return True
    
    def print_receipt(self, receipt_data):
        logger.info(f"打印小票: {receipt_data.get('order_no')}")
        return True
    
    def open_cash_drawer(self):
        logger.info("打开钱箱")
        return True
