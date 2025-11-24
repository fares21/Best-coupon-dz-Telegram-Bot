#!/usr/bin/env python
# coding: utf-8

import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs

# إعداد البوت وواجهة AliExpress
BOT_TOKEN = "8378063186:AAFKfiZGnnEQhn-8xUr7baDK7aZcQmvEZwc"
AE_APP_KEY = "521886"
AE_APP_SECRET = "T9bjjGVVkxC5DAXJSfRJwKX2BdRXySSf"
AE_TRACKING_ID = "default"

bot = telebot.TeleBot(BOT_TOKEN)

aliexpress = AliexpressApi(
    AE_APP_KEY,
    AE_APP_SECRET,
    models.Language.EN,
    models.Currency.EUR,
    AE_TRACKING_ID
)

# لوحات الأزرار
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data="click")
btn3 = types.InlineKeyboardButton(
    "❤️ اشترك في القناة للمزيد من العروض ❤️",
    url="https://t.me/best_coupons_ali_dz"
)
btn4 = types.InlineKeyboardButton(
    "💰  حمل تطبيق Aliexpress عبر الضغط هنا للحصول على مكافأة 5 دولار  💰",
    url="https://s.click.aliexpress.com/e/_c3ffip2l"
)
keyboardStart.add(btn1, btn2, btn3, btn4)

keyboard = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data="click")
btn3 = types.InlineKeyboardButton(
    "❤️ اشترك في القناة للمزيد من العروض ❤️",
    url="https://t.me/best_coupons_ali_dz"
)
keyboard.add(btn1, btn2, btn3)

keyboard_games = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton(
    " ⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️",
    url="https://s.click.aliexpress.com/e/_c4mL0CbT"
)
keyboard_games.add(btn1)

# /start
@bot.message_handler(commands=["start"])
def welcome_user(message):
    bot.send_message(
        message.chat.id,
        "مرحبا بك، ارسل لنا رابط المنتج الذي تريد شرائه لنوفر لك افضل سعر له 👌 \n",
        reply_markup=keyboardStart
    )

# زر "تخفيض السلة"
@bot.callback_query_handler(func=lambda call: call.data == "click")
def button_click(callback_query):
    bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="..."
    )

    text = (
        "✅1-ادخل الى السلة من هنا:\n"
        " https://s.click.aliexpress.com/e/_c4P3GuL3 \n"
        "✅2-قم باختيار المنتجات التي تريد تخفيض سعرها\n"
        "✅3-اضغط على زر دفع ليحولك لصفحة التأكيد \n"
        "✅4-اضغط على الايقونة في الاعلى وانسخ الرابط هنا في البوت لتتحصل على رابط التخفيض"
    )

    img_link1 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
    bot.send_photo(
        callback_query.message.chat.id,
        img_link1,
        caption=text,
        reply_markup=keyboard
    )

# روابط المنتج
def get_affiliate_links(message, message_id, link):
    try:
        # عرض محدود
        limit_links = aliexpress.get_affiliate_links(
            f"https://star.aliexpress.com/share/share.htm"
            f"?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=561&aff_fcid="
        )
        limit_links = limit_links[0].promotion_link

        try:
            products = aliexpress.get_products_details([
                f"https://star.aliexpress.com/share/share.htm"
                f"?platform=AE&businessType=ProductDetail&redirectUrl={link}"
            ])

            product = products[0]
            price_pro = product.target.sale_price
            title_link = product.product_title
            img_link = product.product_main_image_url

            bot.delete_message(message.chat.id, message_id)
            bot.send_photo(
                message.chat.id,
                img_link,
                caption=(
                    " \n🛒 منتجك هو  : 🔥 \n"
                    f"{title_link} 🛍 \n"
                    f"سعر المنتج  : {price_pro} دولار 💵\n"
                    "\nقارن بين الاسعار واشتري 🔥 \n"
                    "♨️ عرض محدود  : \n"
                    f"{limit_links}\n\n"
                    "#AliXPromotion ✅"
                ),
                reply_markup=keyboard
            )

        except Exception:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(
                message.chat.id,
                "قارن بين الاسعار واشتري 🔥 \n"
                "♨️ عرض محدود : \n"
                f"{limit_links}\n\n"
                "#AliXPromotion ✅",
                reply_markup=keyboard
            )

    except Exception:
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# استخراج الرابط من نص الرسالة
def extract_link(text):
    link_pattern = r"https?://\S+|www\.\S+"
    links = re.findall(link_pattern, text or "")
    if links:
        return links[0]
    return None

# بناء رابط السلة
def build_shopcart_link(link):
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params.get("availableProductShopcartIds", [])),
        "extraParams": json.dumps(
            {"channelInfo": {"sourceType": "620"}},
            separators=(",", ":")
        )
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

def get_url_params(link):
    parsed_url = urlparse(link)
    params = parse_qs(parsed_url.query)
    return params

def create_query_string_url(link, params):
    return link + urllib.parse.urlencode(params)

# تخفيض السلة
def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link

        text2 = "هذا رابط تخفيض السلة \n" f"{affiliate_link}"

        img_link3 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
        bot.send_photo(message.chat.id, img_link3, caption=text2)

    except Exception:
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# استقبال أي رسالة
@bot.message_handler(func=lambda message: True)
def get_link(message):
    link = extract_link(message.text)

    sent_message = bot.send_message(
        message.chat.id,
        "المرجو الانتظار قليلا، يتم تجهيز العروض ⏳"
    )
    message_id = sent_message.message_id

    if link and "aliexpress.com" in link.lower() and "p/shoppingcart" not in message.text.lower():
        if "availableProductShopcartIds" in message.text:
            get_affiliate_shopcart_link(link, message)
            return
        get_affiliate_links(message, message_id, link)
    else:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(
            message.chat.id,
            "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n"
            " قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج",
            parse_mode="HTML"
        )

# زر الألعاب (أي callback آخر غير click)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    # لو داتا "games" أو أي شيء آخر غير "click"
    if call.data == "games":
        img_link2 = "https://i.postimg.cc/zvDbVTS0/photo-5893070682508606110-x.jpg"
        bot.send_photo(
            call.message.chat.id,
            img_link2,
            caption=(
                "روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، "
                "قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇"
            ),
            reply_markup=keyboard_games
        )
    else:
        bot.answer_callback_query(call.id, "👍")

# تشغيل السيرفر الصغير + البوت
from keep_alive import keep_alive

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
