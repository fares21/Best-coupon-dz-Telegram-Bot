#!/usr/bin/env python
# coding: utf-8

import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs
import requests
import time

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

# تخزين مؤقت لنتائج البحث
user_searches = {}

# لوحات الأزرار المحدثة
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("🔍 بحث عن منتج", callback_data="search")
btn2 = types.InlineKeyboardButton("🔥 العروض الحارة", callback_data="hot_deals")
btn3 = types.InlineKeyboardButton(
    "❤️ اشترك في القناة للمزيد من العروض ❤️",
    url="https://t.me/best_coupons_ali_dz"
)
btn4 = types.InlineKeyboardButton(
    "💰 حمل تطبيق Aliexpress للحصول على مكافأة  💰",
    url="https://s.click.aliexpress.com/e/_c3ffip2l"
)
keyboardStart.add(btn1, btn2, btn3, btn4)

keyboard = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("🔍 بحث عن منتج", callback_data="search")
btn2 = types.InlineKeyboardButton("🔥 العروض الحارة", callback_data="hot_deals")
btn3 = types.InlineKeyboardButton(
    "❤️ اشترك في القناة للمزيد من العروض ❤️",
    url="https://t.me/best_coupons_ali_dz"
)
keyboard.add(btn1, btn2, btn3)

# /start
@bot.message_handler(commands=["start"])
def welcome_user(message):
    welcome_text = """
🤖 **مرحباً بك في بوت AliExpress للتسويق بالعمولة**

🎯 **كيفية الاستخدام:**
🔍 أرسل رابط منتج AliExpress مباشرة
🔍 أو استخدم /search للبحث عن منتج
🔥 أو استخدم /deals للعروض الخاصة

💡 **مميزات البوت:**
✅ إنشاء روابط عمولة متعددة
✅ أفضل العروض والتخفيضات
✅ بحث متقدم عن المنتجات
✅ دعم عربي كامل

💰 **اربح عمولات على كل عملية شراء!**
    """
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboardStart,
        parse_mode='Markdown'
    )

# البحث عن المنتجات
@bot.message_handler(commands=["search"])
def search_products(message):
    try:
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            msg = bot.reply_to(message, "🔍 يرجى إدخال كلمة للبحث:\nمثال: /search ساعة ذكية")
            bot.register_next_step_handler(msg, process_search)
            return
        
        keyword = command_parts[1].strip()
        process_search_with_keyword(message, keyword)
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

def process_search(msg):
    """معالجة البحث بعد إدخال الكلمة"""
    try:
        if msg.text.startswith('/'):
            return
            
        keyword = msg.text.strip()
        process_search_with_keyword(msg, keyword)
        
    except Exception as e:
        bot.reply_to(msg, f"❌ حدث خطأ في البحث: {str(e)}")

def process_search_with_keyword(message, keyword):
    """معالجة البحث بكلمة مفتاحية"""
    search_msg = bot.reply_to(message, f"🔍 جاري البحث عن: '{keyword}'...")
    
    try:
        # البحث باستخدام API
        products = aliexpress.get_products(keywords=keyword, page_size=10)
        
        if not products:
            bot.edit_message_text(
                f"❌ لم أجد منتجات تطابق بحثك: '{keyword}'",
                chat_id=message.chat.id,
                message_id=search_msg.message_id
            )
            return
        
        # حفظ نتائج البحث
        user_searches[message.chat.id] = {
            'products': products,
            'query': keyword
        }
        
        # عرض النتائج
        response = f"📦 نتائج البحث عن: '{keyword}'\n\n"
        
        for i, product in enumerate(products[:5], 1):
            title = product.product_title[:60] + "..." if len(product.product_title) > 60 else product.product_title
            price = product.target_sale_price
            discount = getattr(product, 'target_discount', '0')
            
            response += f"{i}. {title}\n"
            response += f"   💰 السعر: ${price} | 🏷️ خصم: {discount}%\n\n"
        
        response += "👉 أرسل /product [رقم المنتج] للحصول على روابط التخفيضات"
        
        bot.edit_message_text(
            response,
            chat_id=message.chat.id,
            message_id=search_msg.message_id
        )
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ حدث خطأ في البحث: {str(e)}",
            chat_id=message.chat.id,
            message_id=search_msg.message_id
        )

# عرض المنتج بروابط متعددة
@bot.message_handler(commands=["product"])
def show_product_links(message):
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.reply_to(message, "❌ يرجى إدخال رقم المنتج\nمثال: /product 1")
            return
        
        product_num = int(command_parts[1])
        user_id = message.chat.id
        
        if user_id not in user_searches:
            bot.reply_to(message, "❌ لم تقم بالبحث بعد. استخدم /search أولاً")
            return
        
        products = user_searches[user_id]['products']
        
        if product_num < 1 or product_num > len(products):
            bot.reply_to(message, f"❌ رقم المنتج يجب أن يكون بين 1 و {len(products)}")
            return
        
        product = products[product_num - 1]
        processing_msg = bot.reply_to(message, "🔄 جاري تجهيز روابط التخفيضات...")
        
        # إنشاء روابط متعددة
        product_url = f"https://www.aliexpress.com/item/{product.product_id}.html"
        
        try:
            # إنشاء روابط عمولة مختلفة
            promotion_links = aliexpress.get_affiliate_links([
                product_url,
                f"https://www.aliexpress.com/item/{product.product_id}.html?sourceType=561",
                f"https://www.aliexpress.com/item/{product.product_id}.html?sourceType=620"
            ])
        except:
            promotion_links = []

        # بناء الرسالة بنفس التنسيق المطلوب
        message_text = f"🛒 منتجك هو : 🔥 \n{product.product_title}  {getattr(product, 'target_discount', '0')}% 🛍\n\n"

        # إضافة الروابط المختلفة
        link_names = [
            "رابط تخفيض من صفحة العملات",
            "رابط تخفيض BundleDeals", 
            "رابط تخفيض آخر",
            "رابط تخفيض Super Deals",
            "رابط تخفيض Limited",
            "رابط تخفيض Big Save"
        ]

        for i, link_name in enumerate(link_names):
            if promotion_links and i < len(promotion_links):
                promo_link = promotion_links[i].promotion_link
            else:
                # رابط افتراضي
                promo_link = f"https://s.click.aliexpress.com/deep_link.htm?aff_id={AE_TRACKING_ID}&product_id={product.product_id}"
            
            message_text += f"{link_name} :\n{promo_link}\n\n"

        message_text += "تجد المنتج في يسار الصفحة 👈"

        # إرسال مع الصورة إذا كانت متوفرة
        try:
            bot.send_photo(
                message.chat.id,
                product.product_main_image_url,
                caption=message_text,
                reply_markup=keyboard
            )
            bot.delete_message(message.chat.id, processing_msg.message_id)
        except:
            bot.edit_message_text(
                message_text,
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                reply_markup=keyboard
            )
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# العروض الحارة
@bot.message_handler(commands=["deals"])
def show_hot_deals(message):
    try:
        deals_msg = bot.reply_to(message, "🔥 جاري البحث عن العروض الحارة...")
        
        # الحصول على المنتجات الرائجة
        hot_products = aliexpress.get_hotproducts(country="US", page_size=10)
        
        if not hot_products:
            bot.edit_message_text(
                "❌ لا توجد عروض حالياً",
                chat_id=message.chat.id,
                message_id=deals_msg.message_id
            )
            return
        
        response = "🔥 **العروض الحارة اليوم:**\n\n"
        
        for i, product in enumerate(hot_products[:5], 1):
            title = product.product_title[:50] + "..." if len(product.product_title) > 50 else product.product_title
            price = product.target_sale_price
            discount = getattr(product, 'target_discount', '0')
            
            response += f"{i}. {title}\n"
            response += f"   💰 ${price} | 🏷️ خصم {discount}%\n\n"
        
        response += "👉 أرسل /product [رقم] للحصول على روابط التخفيضات"
        
        # حفظ نتائج العروض
        user_searches[message.chat.id] = {
            'products': hot_products,
            'query': 'hot_deals'
        }
        
        bot.edit_message_text(
            response,
            chat_id=message.chat.id,
            message_id=deals_msg.message_id,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# معالجة الروابط المباشرة
def get_affiliate_links(message, message_id, link):
    try:
        # إنشاء روابط متعددة
        promotion_links = aliexpress.get_affiliate_links([
            link,
            f"{link}?sourceType=561",
            f"{link}?sourceType=620",
            f"{link}?sourceType=580"
        ])

        try:
            products = aliexpress.get_products_details([link])
            product = products[0]
            
            # بناء الرسالة بنفس التنسيق المطلوب
            message_text = f"🛒 منتجك هو : 🔥 \n{product.product_title}  {getattr(product, 'target_discount', '0')}% 🛍\n\n"
            
            # إضافة الروابط المختلفة
            link_names = [
                "رابط تخفيض من صفحة العملات",
                "رابط تخفيض BundleDeals", 
                "رابط تخفيض آخر",
                "رابط تخفيض Super Deals"
            ]
            
            for i, link_name in enumerate(link_names):
                if i < len(promotion_links):
                    promo_link = promotion_links[i].promotion_link
                    message_text += f"{link_name} :\n{promo_link}\n\n"
            
            message_text += "تجد المنتج في يسار الصفحة 👈"
            
            bot.delete_message(message.chat.id, message_id)
            bot.send_photo(
                message.chat.id,
                product.product_main_image_url,
                caption=message_text,
                reply_markup=keyboard
            )

        except Exception as e:
            # إذا فشل جلب تفاصيل المنتج، إرسال الروابط فقط
            bot.delete_message(message.chat.id, message_id)
            message_text = "🛒 روابط التخفيضات للمنتج:\n\n"
            
            for i, promo_link in enumerate(promotion_links[:4]):
                link_name = ["رابط تخفيض 1", "رابط تخفيض 2", "رابط تخفيض 3", "رابط تخفيض 4"][i]
                message_text += f"{link_name} :\n{promo_link.promotion_link}\n\n"
            
            bot.send_message(
                message.chat.id,
                message_text,
                reply_markup=keyboard
            )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

# استخراج الرابط من نص الرسالة
def extract_link(text):
    link_pattern = r"https?://\S+|www\.\S+"
    links = re.findall(link_pattern, text or "")
    if links:
        return links[0]
    return None

# استقبال أي رسالة
@bot.message_handler(func=lambda message: True)
def get_link(message):
    # تجاهل الأوامر
    if message.text.startswith('/'):
        return
        
    link = extract_link(message.text)

    if link and "aliexpress.com" in link.lower():
        sent_message = bot.send_message(
            message.chat.id,
            "🔄 جاري تجهيز روابط التخفيضات..."
        )
        get_affiliate_links(message, sent_message.message_id, link)
    else:
        bot.reply_to(
            message,
            "🔍 أرسل رابط منتج AliExpress مباشرة\n"
            "أو استخدم /search للبحث عن منتج\n"
            "أو /deals للعروض الخاصة",
            reply_markup=keyboard
        )

# معالجة الأزرار الجديدة
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "search":
        msg = bot.send_message(
            call.message.chat.id,
            "🔍 أدخل كلمة للبحث عن منتج:"
        )
        bot.register_next_step_handler(msg, process_search)
        
    elif call.data == "hot_deals":
        show_hot_deals(call.message)
        
    else:
        bot.answer_callback_query(call.id, "👍")

# تشغيل السيرفر الصغير + البوت
from keep_alive import keep_alive

if __name__ == "__main__":
    keep_alive()
    print("✅ البوت يعمل الآن...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
