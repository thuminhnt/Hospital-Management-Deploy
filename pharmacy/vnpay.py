import hashlib
import hmac
import urllib.parse
import datetime
import random
from django.conf import settings

def get_vnpay_payment_url(order_id, amount, order_desc, bank_code=None, language="vn"):
    """
    Tạo URL thanh toán VNPay
    """
    vnp_params = {}
    vnp_params['vnp_Version'] = '2.1.0'
    vnp_params['vnp_Command'] = 'pay'
    vnp_params['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
    vnp_params['vnp_Amount'] = int(float(amount) * 100)  # Chuyển sang VND, nhân 100 theo tài liệu VNPay
    vnp_params['vnp_CurrCode'] = 'VND'
    vnp_params['vnp_TxnRef'] = str(order_id)
    vnp_params['vnp_OrderInfo'] = order_desc
    vnp_params['vnp_OrderType'] = 'billpayment'
    
    # Lấy thời gian hiện tại từ múi giờ Việt Nam
    currtime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    vnp_params['vnp_CreateDate'] = currtime.strftime('%Y%m%d%H%M%S')
    
    # Tạo thời gian hết hạn (15 phút từ bây giờ)
    expiry_time = currtime + datetime.timedelta(minutes=15)
    vnp_params['vnp_ExpireDate'] = expiry_time.strftime('%Y%m%d%H%M%S')
    
    # IP của người dùng, trong môi trường phát triển dùng 127.0.0.1
    vnp_params['vnp_IpAddr'] = '127.0.0.1'
    vnp_params['vnp_Locale'] = language
    vnp_params['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL
    
    if bank_code:
        vnp_params['vnp_BankCode'] = bank_code

    # Sắp xếp các tham số theo khóa trước khi ký
    param_keys = sorted(vnp_params.keys())
    # Tạo chuỗi query đã URL encode
    hashdata = "&".join([f"{k}={urllib.parse.quote_plus(str(vnp_params[k]))}" for k in param_keys])
    
    # Tạo chữ ký
    hmac_code = hmac.new(
        bytes(settings.VNPAY_HASH_SECRET_KEY, 'utf-8'),
        bytes(hashdata, 'utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    vnp_params['vnp_SecureHash'] = hmac_code
    
    # Xây dựng URL thanh toán
    payment_url = settings.VNPAY_PAYMENT_URL + "?" + "&".join([f"{k}={urllib.parse.quote_plus(str(vnp_params[k]))}" for k in vnp_params.keys()])
    
    return payment_url

def validate_payment_response(request_params):
    """
    Xác minh tính toàn vẹn của dữ liệu trả về từ VNPay
    """
    # Chuyển đổi QueryDict sang dictionary
    data = dict(request_params)
    
    # Đảm bảo lấy giá trị đầu tiên nếu là list
    data = {k: v[0] if isinstance(v, list) else v for k, v in data.items()}
    
    # Loại bỏ SecureHash khỏi quá trình xác thực
    if 'vnp_SecureHash' in data:
        secure_hash = data['vnp_SecureHash']
        del data['vnp_SecureHash']
    else:
        return False, "Không tìm thấy mã băm bảo mật"
    
    # Sắp xếp các tham số theo thứ tự alphabet
    sorted_keys = sorted(data.keys())
    
    # Tạo chuỗi hash data
    hashdata = "&".join([f"{k}={urllib.parse.quote_plus(str(data[k]))}" for k in sorted_keys])
    
    # Tạo chữ ký
    hmac_code = hmac.new(
        bytes(settings.VNPAY_HASH_SECRET_KEY, 'utf-8'),
        bytes(hashdata, 'utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    # Debug: In ra để kiểm tra
    print("Original Secure Hash:", secure_hash)
    print("Calculated Hash:", hmac_code)
    
    # So sánh chữ ký
    return hmac_code == secure_hash, "Xác minh thanh toán"