import os
from flask import Flask, request, jsonify
import requests
import urllib.parse
from datetime import datetime
import json
import re

app = Flask(__name__)

# --- إعدادات واتساب محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"

# قاموس ترجمة المدن
CITY_MAP = {
    "67b9e47c7e7fbc758fd244ea": "الحديدة",
    "67b9e47c7e7fbc758fd244eb": "عدن",
    "67b9e47c7e7fbc758fd244ec": "صنعاء",
    "67b9e47c7e7fbc758fd244ed": "تعز",
    "67b9e47c7e7fbc758fd244ee": "حضرموت"
}

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def get_real_text(val, field_name=""):
    txt = str(val).strip()
    if not txt or txt.lower() in ['none', 'null', '']: return None
    if field_name == "city" and txt in CITY_MAP: return CITY_MAP[txt]
    if len(txt) >= 15 and re.match(r'^[a-f0-9]+$', txt): return None
    return txt

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
        full_time = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

        status_info = smart_parse(order.get('status', {}))
        status_title = status_info.get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        extra_note = ""
        st = status_title
        
        if not is_paid and not any(x in st for x in ["إلغاء", "ملغي", "مرتجع"]):
            extra_note = "\n⚠️ *يرجى تزويدنا بصورة القسيمة المالية (إيصال السداد) هنا لمتابعة تنفيذ طلبكم.*"
        elif any(x in st for x in ["إلغاء", "ملغي"]):
            extra_note = "\n🚫 *إشعار:* نأسف لإبلاغكم بأنه تم إلغاء الطلب. لمزيد من المعلومات يرجى التواصل معنا."
        elif any(x in st for x in ["إرجاع", "استرداد", "مرتجع"]):
            extra_note = "\n💰 *ملاحظة:* سيتم استرداد المبلغ إلى حسابكم خلال 48 ساعة عمل." if is_paid else "\n💰 *ملاحظة:* تم اعتماد الاسترجاع في حسابكم لدينا."
        elif any(x in st for x in ["شحن", "تم الإرسال"]):
            extra_note = "\n🚚 *إشعار:* تم تسليم طلبكم لشركة الشحن، وهو في الطريق إليكم الآن."

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        if event == "order.created":
            country = get_real_text(customer.get('countryName')) or "اليمن"
            city = get_real_text(customer.get('cityName')) or get_real_text(customer.get('city'), "city")
            district = get_real_text(customer.get('district')) or get_real_text(customer.get('address1'))
            street = get_real_text(customer.get('street')) or get_real_text(customer.get('address2'))
            addr_parts = [p for p in [country, city, district, street] if p]
            full_address = " - ".join(addr_parts)
            
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
                f"🕒 *التوقيت:* `{full_time}`\n"
                f"🔗 *رابط التتبع:* {tracking_link}\n\n"
                f"{footer}"
            )
        else:
            header = "🔄 *إشعار نظام: تحديث الطلب*"
            msg = (
                f"{header}\n"
                f"{divider}\n"
                f"📦 *رقم المنتج:* `{order_id}`\n"
                f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
                f"📝 *حالة الدفع:* {pay_text}"
                f"{extra_note}\n"
                f"{divider}\n"
                f"🕒 *التوقيت:* `{full_time}`\n"
                f"🔗 *تتبع:* {tracking_link}\n\n"
                f"{footer}"
            )

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
