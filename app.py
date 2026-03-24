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
def mahjoub_final_v41():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    
    try:
        payload = smart_parse(request.get_data(as_text=True))
        order = smart_parse(payload.get('data', payload))
        customer = smart_parse(order.get('customer', order.get('salesLead', {})))
        
        # استخراج المعرف الفريد (الموجود في الرابط الذي أرسلته)
        order_internal_id = order.get('_id') 
        # رقم الطلب الظاهري (1000000xxx)
        order_handle = str(order.get('handle') or order.get('handel') or "0000")
        
        phone = customer.get('phone1') or customer.get('phone2') or order.get('phone')
        phone = str(phone).replace('+', '').replace(' ', '') if phone else ""
        if phone and not phone.startswith('967'): phone = '967' + phone

        # --- الرابط الصحيح للعملاء ---
        # نستخدم المعرف الداخلي لفتح الفاتورة مباشرة للعميل
        pdf_link = f"https://mahjoub.online/orders/invoice/{order_internal_id}"
        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_handle}"
        
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 

        status_title = order.get('status_name') or smart_parse(order.get('status', {})).get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        extra_note = ""
        if not is_paid and not any(x in status_title for x in ["إلغاء", "ملغي"]):
            extra_note = "\n⚠️ *يرجى تزويدنا بصورة إيصال السداد هنا لمتابعة تنفيذ طلبكم.*"

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        msg = (
            "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
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
            f"{extra_note}\n"
            f"{divider}\n"
            f"🕒 *توقيت الطلب:* `{full_time}`\n"
            f"🔗 *رابط التتبع:* {tracking_link}\n\n"
            f"📦 *مرفق أدناه رابط فاتورة PDF إلكترونية لطلبكم:*\n"
            f"{pdf_link}\n\n"
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
