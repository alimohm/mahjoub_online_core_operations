import os
from flask import Flask, request, jsonify
import requests
import urllib.parse
from datetime import datetime, timedelta
import json

app = Flask(__name__)

TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_perfect_flow():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    
    try:
        payload = smart_parse(request.get_data(as_text=True))
        order = smart_parse(payload.get('data', payload))
        customer = smart_parse(order.get('customer', order.get('salesLead', {})))
        
        # الرقم المتغير (مثل 1000000930)
        order_handle = str(order.get('handle') or "0000")
        
        phone = customer.get('phone1') or customer.get('phone2') or order.get('phone')
        phone = str(phone).replace('+', '').replace(' ', '') if phone else ""
        if phone and not phone.startswith('967'): phone = '967' + phone

        # --- الرابط المضمون الذي يفتح للعملاء ---
        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_handle}"
        
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 

        status_title = order.get('status_name') or smart_parse(order.get('status', {})).get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        # صياغة الرسالة لتوجه العميل لكيفية استخراج الفاتورة
        msg = (
            "✨ *إشعار نظام: تم إنشاء طلب جديد بنجاح* ✨\n\n"
            f"🧾 *فاتورة رقم:* `{order_handle}`\n"
            f"{divider}\n"
            f"👤 *العميل:* {customer.get('name', 'عميلنا العزيز')}\n"
            f"📍 *موقع التوصيل:* {customer.get('cityName', 'اليمن')} - {customer.get('district', 'الشارع')}\n"
            f"{divider}\n"
            f"💰 *الضريبة:* `{order.get('taxAmount', 0)}` ريال\n"
            f"💵 *الإجمالي النهائي:* `{order.get('total', 0)}` ريال\n"
            f"{divider}\n"
            f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
            f"📝 *حالة الدفع:* {pay_text}\n"
            f"{divider}\n"
            f"🕒 *توقيت الطلب:* `{full_time}`\n\n"
            f"🔗 *لتتبع حالة المنتج وتحميل فاتورتك التفصيلية:* \n{tracking_link}\n\n"
            f"💡 *ملاحظة:* لتحميل الفاتورة PDF التي تحتوي على بياناتك الكاملة، يرجى الضغط على زر (طباعة الفاتورة) داخل الرابط أعلاه.\n\n"
            f"{footer}"
        )

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
