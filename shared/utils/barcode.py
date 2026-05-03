import barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO
from PIL import Image

def generate_barcode(data, barcode_type='code128', output_format='png'):
    try:
        CodeClass = barcode.get_barcode_class(barcode_type)
        code = CodeClass(data, writer=ImageWriter())
        
        buffer = BytesIO()
        code.write(buffer)
        buffer.seek(0)
        
        return Image.open(buffer)
    except Exception as e:
        from core.logger import logger
        logger.error(f"生成条码失败: {e}")
        return None

def generate_qrcode(data, size=200, box_size=10, border=4):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    except Exception as e:
        from core.logger import logger
        logger.error(f"生成二维码失败: {e}")
        return None

def save_image(image, file_path):
    try:
        image.save(file_path)
        return True
    except Exception as e:
        from core.logger import logger
        logger.error(f"保存图片失败: {e}")
        return False
