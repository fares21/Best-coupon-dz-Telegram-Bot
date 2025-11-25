from flask import Flask
import threading
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)  # استخدم port 8080 بدلاً من 10000

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
