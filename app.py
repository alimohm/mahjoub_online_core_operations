import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import re
from fpdf import FPDF # مكتبة صناعة الـ PDF

app = Flask(__name__)

# --- إعدادات واتساب محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"
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

# --- وظيفة صناعة ملف PDF بسيط لحظياً ---
def generate_simple_invoice(order_id, customer_name, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="MAHJOUB ONLINE", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Invoice Number: {order_id}", ln=1)
    pdf.cell(200, 10, txt=f"Customer: {customer_name}", ln=1)
    pdf.cell(200, 10, txt=f"Total Amount: {total} SAR", ln=1)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
    
    file_name = "invoice_order.pdf"
    pdf.output(file_name)
    return file_name

# --- بوابة تحميل الملفات ---
@app.route('/download/<path:filename>')
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
        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_id}"
        
        # --- التوقيت اليمني (حافطنا عليه) ---
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 
        
        status_info = smart_parse(order.get('status', {}))
        status_title = status_info.get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        extra_note = ""
        st = status_title
        
        # --- الملاحظات الذكية (حافظنا عليها) ---
        if not is_paid and not any(x in st for x in ["إلغاء", "ملغي", "مرتجع"]):
            extra_note = "\n⚠️ *يرجى تزويدنا بصورة القسيمة المالية (إيصال السداد) هنا لمتابعة تنفيذ طلبكم.*"
        elif any(x in st for x in ["إلغاء", "ملغي"]):
            extra_note = "\n🚫 *إشعار:* نأسف لإبلاغكم بأنه تم إلغاء الطلب."
        elif any(x in st for x in ["شحن", "تم الإرسال"]):
            extra_note = "\n🚚 *إشعار:* تم تسليم طلبكم لشركة الشحن، وهو في الطريق إليكم."

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        if event == "order.created":
            country = get_real_text(customer.get('countryName'))
            city = get_real_text(customer.get('cityName'))
            district = get_real_text(customer.get('district')) or get_real_text(customer.get('address1'))
            street = get_real_text(customer.get('street')) or get_real_text(customer.get('address2'))
            
            addr_parts = [p for p in [country, city, district, street] if p]
            full_address = " - ".join(addr_parts) if addr_parts else "اليمن"
            
            # --- نص الرسالة الكامل المعتاد ---
            msg = (
                "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
                f"🧾 *فاتورة رقم:* `{order_id}`\n"
                f"{divider}\n"
                f"👤 *العميل:* {customer.get('firstName', '')} {customer.get('lastName', '')}\n"
                f"📍 *موقع التوصيل:* {full_address}\n"
                f"{divider}\n"
                f"💰 *الضريبة:* `{order.get('taxAmount', 0)}` ريال\n"
                f"💵 *الإجمالي النهائي:* `{order.get('priceWithShipping', 0)}` ريال\n"
                f"{divider}\n"
                f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
                f"📝 *حالة الدفع:* {pay_text}"
                f"{extra_note}\n"
                f"{divider}\n"
                f"🕒 *توقيت الطلب:* `{full_time}`\n"
                f"🔗 *رابط التتبع:* {tracking_link}\n\n"
                "📦 *مرفق أدناه فاتورة PDF إلكترونية لطلبكم.*\n"
                f"{footer}"
            )
        else:
            msg = (
                "🔄 *إشعار نظام: تحديث الطلب*\n"
                f"{divider}\n"
                f"📦 *رقم المنتج:* `{order_id}`\n"
                f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
                f"📝 *حالة الدفع:* {pay_text}"
                f"{extra_note}\n"
                f"{divider}\n"
                f"🕒 *وقت التحديث:* `{full_time}`\n"
                f"🔗 *تتبع:* {tracking_link}\n\n"
                f"{footer}"
            )

        # إرسال النص
        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

            # --- إرسال ملف الـ PDF عند إنشاء طلب جديد فقط ---
            if event == "order.created":
                full_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}"
                total_price = order.get('priceWithShipping', 0)
                
                # إنشاء الملف
                invoice_file = generate_simple_invoice(order_id, full_name, total_price)
                
                # رابط الملف
                pdf_link = f"{BASE_URL}/download/{invoice_file}"
                
                # أمر إرسال الوثيقة
                file_api = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&document={urllib.parse.quote(pdf_link)}"
                requests.get(file_api, timeout=15)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
