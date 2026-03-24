import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import re

app = Flask(__name__)

# --- إعدادات محجوب أونلاين ---
# استبدل هذا بالرابط الخاص بك في Render
BASE_URL = "https://mahjoub-bot.onrender.com" 

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def get_real_text(val):
    txt = str(val).strip()
    if not txt or txt.lower() in ['none', 'null', '', 'false']: return None
    return txt

# --- بوابة تحميل ملف test.pdf من GitHub ---
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(os.getcwd(), filename)

@app.route('/')
def home():
    return "سيرفر محجوب أونلاين يعمل بنجاح", 200

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
        
        # --- التوقيت اليمني (GMT+3) ---
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 
        
        status_info = smart_parse(order.get('status', {}))
        status_title = status_info.get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        if event == "order.created":
            # رابط الفاتورة المباشر من سيرفرك
            pdf_link = f"{BASE_URL}/download/test.pdf"
            
            msg = (
                "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
                f"🧾 *فاتورة رقم:* `{order_id}`\n"
                f"{divider}\n"
                f"👤 *العميل:* {customer.get('firstName', '')} {customer.get('lastName', '')}\n"
                f"💵 *الإجمالي:* `{order.get('priceWithShipping', 0)}` ريال\n"
                f"{divider}\n"
                f"🚚 *الحالة:* 【 {status_title} 】\n"
                f"📝 *الدفع:* {pay_text}\n"
                f"🕒 *الوقت:* `{full_time}`\n"
                f"{divider}\n"
                f"📄 *رابط تحميل الفاتورة PDF:*\n{pdf_link}\n\n"
                f"{footer}"
            )
            
            # سجل الرسالة في Render Logs للتأكد من المحتوى
            print(f"--- رسالة جاهزة للإرسال إلى {phone} ---\n{msg}")

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"خطأ في السيرفر: {e}")
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
