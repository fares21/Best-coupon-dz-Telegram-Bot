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
import os
import sys
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعداد البوت وواجهة AliExpress
BOT_TOKEN = "8378063186:AAFKfiZGnnEQhn-8xUr7baDK7aZcQmvEZwc"
AE_APP_KEY = "521886"
AE_APP_SECRET = "T9bjjGVVkxC5DAXJSfRJwKX2BdRXySSf"
AE_TRACKING_ID = "default"

# تهيئة البوت
bot = telebot.TeleBot(BOT_TOKEN)

# تهيئة AliExpress API
try:
    aliexpress = AliexpressApi(
        AE_APP_KEY,
        AE_APP_SECRET,
        models.Language.EN,
        models.Currency.EUR,
        AE_TRACKING_ID
    )
    logger.info("✅ AliExpress API initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize AliExpress API: {e}")
    aliexpress = None

# تخزين مؤقت لنتائج البحث
user_searches = {}

# لوحات الأزرار المحدثة
def create_keyboards():
    keyboardStart = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🔍 بحث عن منتج", callback_data="search")
    btn2 = types.InlineKeyboardButton("🔥 العروض الحارة", callback_data="hot_deals")
    btn3 = types.InlineKeyboardButton(
        "❤️ اشترك في القناة للمزيد من العروض ❤️",
        url="https://t.me/best_coupons_ali_dz"
    )
    btn4 = types.InlineKeyboardButton(
        "💰 حمل تطبيق Aliexpress للحصول على مكافأة 💰",
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
    
    return keyboardStart, keyboard

keyboardStart, keyboard = create_keyboards()

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
    
    try:
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=keyboardStart,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Sent welcome message to user {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error sending welcome message: {e}")

# معالجة الروابط المباشرة
def get_affiliate_links(message, message_id, link):
    try:
        if not aliexpress:
            bot.edit_message_text(
                "❌ خدمة API غير متاحة حالياً",
                chat_id=message.chat.id,
                message_id=message_id
            )
            return

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
                "رابط تخفيض Super Deals",
                "رابط تخفيض Limited",
                "رابط تخفيض Big Save"
            ]
            
            for i, link_name in enumerate(link_names):
                if i < len(promotion_links):
                    promo_link = promotion_links[i].promotion_link
                else:
                    # رابط افتراضي
                    promo_link = f"https://s.click.aliexpress.com/deep_link.htm?aff_id={AE_TRACKING_ID}&product_id={getattr(product, 'product_id', '')}"
                
                message_text += f"{link_name} :\n{promo_link}\n\n"

            message_text += "تجد المنتج في يسار الصفحة 👈"
            
            bot.delete_message(message.chat.id, message_id)
            # حاول إرسال الصورة أولاً
            try:
                bot.send_photo(
                    message.chat.id,
                    product.product_main_image_url,
                    caption=message_text,
                    reply_markup=keyboard
                )
            except:
                # إذا فشل إرسال الصورة، أرسل النص فقط
                bot.send_message(
                    message.chat.id,
                    message_text,
                    reply_markup=keyboard
                )

        except Exception as e:
            # إذا فشل جلب تفاصيل المنتج، إرسال الروابط فقط
            logger.error(f"Product details error: {e}")
            bot.delete_message(message.chat.id, message_id)
            message_text = "🛒 روابط التخفيضات للمنتج:\n\n"
            
            for i, promo_link in enumerate(promotion_links[:6]):
                link_name = ["رابط تخفيض 1", "رابط تخفيض 2", "رابط تخفيض 3", "رابط تخفيض 4", "رابط تخفيض 5", "رابط تخفيض 6"][i]
                message_text += f"{link_name} :\n{promo_link.promotion_link}\n\n"
            
            message_text += "تجد المنتج في يسار الصفحة 👈"
            
            bot.send_message(
                message.chat.id,
                message_text,
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Affiliate links error: {e}")
        try:
            bot.edit_message_text(
                "❌ حدث خطأ في معالجة الرابط، يرجى المحاولة لاحقاً",
                chat_id=message.chat.id,
                message_id=message_id
            )
        except:
            bot.send_message(
                message.chat.id,
                "❌ حدث خطأ في معالجة الرابط، يرجى المحاولة لاحقاً"
            )

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
        try:
            sent_message = bot.send_message(
                message.chat.id,
                "🔄 جاري تجهيز روابط التخفيضات..."
            )
            get_affiliate_links(message, sent_message.message_id, link)
        except Exception as e:
            logger.error(f"Error processing link: {e}")
            bot.reply_to(message, "❌ حدث خطأ في معالجة الرابط")
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
    try:
        if call.data == "search":
            msg = bot.send_message(
                call.message.chat.id,
                "🔍 أرسل رابط منتج AliExpress مباشرة\nأو استخدم /search للبحث"
            )
            
        elif call.data == "hot_deals":
            bot.send_message(
                call.message.chat.id,
                "🔥 أرسل رابط أي منتج للحصول على أفضل العروض!"
            )
            
        bot.answer_callback_query(call.id, "✅")
    except Exception as e:
        logger.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ")

# تشغيل البوت مع معالجة الأخطاء
def run_bot():
    logger.info("🚀 Starting Telegram Bot...")
    
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Attempt {attempt + 1} to start bot...")
            
            # استخدم polling بدلاً من infinity_polling مع skip_pending
            bot.polling(
                timeout=10,
                long_polling_timeout=5,
                skip_pending=True  # تجاهل الرسائل المعلقة
            )
            
        except telebot.apihelper.ApiTelegramException as e:
            if "Conflict" in str(e):
                logger.error(f"❌ Another bot instance is running. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # زيادة وقت الانتظار
            else:
                logger.error(f"❌ Telegram API error: {e}")
                break
                
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            time.sleep(retry_delay)
            
    logger.error("❌ Failed to start bot after multiple attempts")

# تشغيل السيرفر الصغير
try:
    from keep_alive import keep_alive
    keep_alive()
    logger.info("✅ Keep-alive server started")
except ImportError:
    logger.warning("⚠️ Keep-alive module not found, running without web server")
except Exception as e:
    logger.error(f"❌ Error starting keep-alive: {e}")

if __name__ == "__main__":
    run_bot()
