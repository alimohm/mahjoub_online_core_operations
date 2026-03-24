import os
from flask import Flask, request, jsonify
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import re

app = Flask(__name__)

# --- الإعدادات الجديدة المحدثة ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"  # مفتاحك الجديد

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def get_real_text(val):
    txt = str(val).strip()
    if not txt or txt.lower() in ['none', 'null', '', 'false']: return None
    return txt

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_auto_receipt_v38():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    
    try:
        raw_data = request.get_data(as_text=True)
        payload = smart_parse(raw_data)
        
        # استخراج بيانات الطلب
        order = smart_parse(payload.get('data', payload))
        # استخراج بيانات العميل (تأكدنا أنها في بعض الأحيان تكون داخل salesLead أو مباشرة)
        customer = smart_parse(order.get('customer', order.get('salesLead', {})))
        
        event = payload.get('event', 'order.updated')
        order_id = order.get('handle', order.get('handel', '0000'))
        
        # محاولة جلب الرقم من phone1 أو phone2 (كما رأينا في السجلات)
        phone = customer.get('phone1') or customer.get('phone2') or order.get('phone')
        phone = str(phone).replace('+', '').replace(' ', '') if phone else ""
        
        # إضافة فتح الخط اليمني إذا لم يكن موجوداً
        if phone and not phone.startswith('967'):
            phone = '967' + phone

        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_id}"
        
        # --- توقيت اليمن (GMT+3) ---
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 

        status_title = order.get('status_name') or smart_parse(order.get('status', {})).get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        extra_note = ""
        st = status_title
        
        if not is_paid and not any(x in st for x in ["إلغاء", "ملغي", "مرتجع"]):
            extra_note = "\n⚠️ *يرجى تزويدنا بصورة إيصال السداد هنا لمتابعة تنفيذ طلبكم.*"
        elif any(x in st for x in ["إلغاء", "ملغي"]):
            extra_note = "\n🚫 *إشعار:* نأسف لإبلاغكم بأنه تم إلغاء الطلب."
        elif any(x in st for x in ["شحن", "تم الإرسال"]):
            extra_note = "\n🚚 *إشعار:* تم تسليم طلبكم لشركة الشحن، وهو في الطريق إليكم."

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        if event == "order.created":
            city = get_real_text(customer.get('cityName'))
            district = get_real_text(customer.get('district')) or get_real_text(customer.get('address1'))
            full_address = f"{city} - {district}" if city and district else (city or "اليمن")
            
            msg = (
                "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
                f"🧾 *فاتورة رقم:* `{order_id}`\n"
                f"{divider}\n"
                f"👤 *العميل:* {customer.get('name', customer.get('firstName', ''))}\n"
                f"📍 *موقع التوصيل:* {full_address}\n"
                f"{divider}\n"
                f"💵 *الإجمالي النهائي:* `{order.get('priceWithShipping', order.get('total', 0))}` ريال\n"
                f"{divider}\n"
                f"🚚 *الحالة:* 【 {status_title} 】\n"
                f"📝 *الدفع:* {pay_text}"
                f"{extra_note}\n"
                f"{divider}\n"
                f"🕒 *توقيت الطلب:* `{full_time}`\n"
                f"🔗 *رابط التتبع:* {tracking_link}\n\n"
                f"{footer}"
            )
        else:
            msg = (
                "🔄 *إشعار نظام: تحديث الطلب*\n"
                f"{divider}\n"
                f"📦 *رقم الطلب:* `{order_id}`\n"
                f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
                f"📝 *حالة الدفع:* {pay_text}"
                f"{extra_note}\n"
                f"{divider}\n"
                f"🕒 *وقت التحديث:* `{full_time}`\n"
                f"🔗 *تتبع:* {tracking_link}\n\n"
                f"{footer}"
            )

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)
            print(f"Success: Message sent to {phone}")

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
