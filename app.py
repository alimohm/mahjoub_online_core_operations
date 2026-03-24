import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import re

app = Flask(__name__)

# --- إعدادات محجوب أونلاين ---
# ملاحظة: بما أنك استغنيت عن TextMeBot، اترك هذه القيم كمرجع أو استبدلها ببيانات الـ API الجديد
BASE_URL = "https://mahjoub-bot.onrender.com" 

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def get_real_text(val):
    txt = str(val).strip()
    if not txt or txt.lower() in ['none', 'null', '', 'false']: return None
    if len(txt) >= 20 and re.match(r'^[a-f0-9]+$', txt): return None
    return txt

# --- بوابة تحميل الملفات (هذا الجزء هو الذي يجعل رابط الـ PDF يعمل) ---
@app.route('/download/<path:filename>')
def download_file(filename):
    # يقوم هذا السطر بالبحث عن ملف test.pdf في مجلد المشروع وإرساله للمتصفح
    return send_from_directory(os.getcwd(), filename)

@app.route('/')
def home():
    return "سيرفر محجوب أونلاين يعمل بنجاح - جاهز لتوزيع الفواتير", 200

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_auto_receipt_v38():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    try:
        raw_data = request.get_data(as_text=True)
        payload = smart_parse(raw_data)
        order = smart_parse(payload.get('data', payload))
        customer = smart_parse(order.get('salesLead', {}))
        
        event = payload.get('event', 'order.created')
        order_id = order.get('handel', '0000')
        phone = str(customer.get('phone1', '')).replace('+', '').replace(' ', '')
        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_id}"
        
        # --- التوقيت اليمني GMT+3 ---
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 
        
        status_info = smart_parse(order.get('status', {}))
        status_title = status_info.get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        extra_note = ""
        if not is_paid and not any(x in status_title for x in ["إلغاء", "ملغي"]):
            extra_note = "\n⚠️ *يرجى تزويدنا بصورة القسيمة المالية (إيصال السداد) هنا لمتابعة تنفيذ طلبكم.*"

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        if event == "order.created":
            city = get_real_text(customer.get('cityName')) or "اليمن"
            district = get_real_text(customer.get('district')) or ""
            full_address = f"{city} - {district}" if district else city
            
            # تجهيز نص الرسالة
            msg = (
                "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
                f"🧾 *فاتورة رقم:* `{order_id}`\n"
                f"{divider}\n"
                f"👤 *العميل:* {customer.get('firstName', '')} {customer.get('lastName', '')}\n"
                f"📍 *موقع التوصيل:* {full_address}\n"
                f"{divider}\n"
                f"💵 *الإجمالي النهائي:* `{order.get('priceWithShipping', 0)}` ريال\n"
                f"{divider}\n"
                f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
                f"📝 *حالة الدفع:* {pay_text}"
                f"{extra_note}\n"
                f"{divider}\n"
                f"🕒 *توقيت الطلب:* `{full_time}`\n"
                f"🔗 *رابط التتبع:* {tracking_link}\n\n"
                "📦 *رابط تحميل فاتورة الـ PDF الخاصة بك:*\n"
                f"{BASE_URL}/download/test.pdf\n\n"
                f"{footer}"
            )
            
            # هنا تضع كود الإرسال الخاص بالخدمة الجديدة التي ستستخدمها بدلاً من TextMeBot
            # مثال: print(msg) لغرض التجربة في الـ Logs
            print(f"إرسال إلى {phone}: \n{msg}")

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
