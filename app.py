import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import re

app = Flask(__name__)

# --- إعدادات محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"

# ⚠️ ملاحظة: استبدل الرابط أدناه برابط تطبيقك الحقيقي من Render
# مثال: https://mahjoub-bot.onrender.com
BASE_URL = "https://mahjoub-bot.onrender.com" 

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def get_real_text(val):
    txt = str(val).strip()
    if not txt or txt.lower() in ['none', 'null', '', 'false']: return None
    return txt

# --- بوابة تحميل الملفات ---
# هذه الوظيفة تسمح لواتساب بسحب ملف الـ PDF من سيرفرك
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(os.getcwd(), filename)

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
        
        # ضبط التوقيت اليمني (GMT+3)
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p")

        if event == "order.created" and phone:
            # 1. صياغة الرسالة النصية
            msg = (
                "✨ *محجوب أونلاين | إشعار طلب جديد* ✨\n\n"
                f"🧾 *رقم الفاتورة:* `{order_id}`\n"
                f"👤 *العميل:* {customer.get('firstName', '')}\n"
                f"🕒 *التوقيت:* `{full_time}`\n\n"
                "📦 *تجد مرفقاً أدناه نسخة PDF من فاتورتك.*"
            )
            
            # إرسال النص
            text_api = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(text_api, timeout=5)

            # 2. إرسال ملف الـ PDF (test.pdf)
            # الرابط المباشر للملف على سيرفرك
            pdf_link = f"{BASE_URL}/download/test.pdf"
            
            # استخدام أمر &document لإرساله كملف وليس كنص
            file_api = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&document={urllib.parse.quote(pdf_link)}"
            
            # تنفيذ إرسال الملف
            requests.get(file_api, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
