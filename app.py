import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# سحب المفاتيح من بيئة رندر
TEXTMEBOT_KEY = os.environ.get('TEXTMEBOT_KEY')
QMR_KEY = os.environ.get('MAHJOUB_ONLINE_KEY')

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def webhook():
    if request.method in ['GET', 'HEAD']:
        return "OK", 200

    data = request.json
    print(f"--- طلب جديد مستلم ---")
    
    # استخراج رقم الهاتف والاسم
    customer = data.get('data', {}).get('customer', {})
    phone = str(customer.get('phone1', '')).replace('+', '').replace(' ', '')
    name = customer.get('name', 'عميلنا العزيز')
    order_id = data.get('data', {}).get('handle', 'بدون رقم')
    status = data.get('data', {}).get('status_name', 'محدثة')

    if not phone or phone == 'None':
        print("خطأ: لم يتم العثور على رقم هاتف")
        return "No Phone", 200

    # تجهيز رسالة محجوب أونلاين الملكية
    msg = f"مرحباً {name} ✨\nتم تحديث حالة طلبك رقم ({order_id}) إلى: *{status}*\nشكراً لاختيارك محجوب أونلاين - سوقك الذكي."
    
    # إرسال عبر TextMeBot
    whatsapp_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_KEY}&text={msg}"
    
    try:
        response = requests.get(whatsapp_url)
        print(f"تم الإرسال للرقم {phone}. رد السيرفر: {response.text}")
    except Exception as e:
        print(f"فشل الإرسال: {str(e)}")

    return "Done", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
