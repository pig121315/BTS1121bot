import time
import threading
from datetime import datetime
import zoneinfo
import cloudscraper
from bs4 import BeautifulSoup
from flask import Flask

# ===== 參數設定 =====
TARGET_URL = "https://tixcraft.com/ticket/area/26_btskns/22763"
TG_TOKEN = "8944538900:AAGLVNGa2ZnCQBJII7tbf05Wqv1mg6BbqHg"

# 【雙重通知清單】同時發送給你（個人）與你的朋友（頻道）
NOTIFICATION_TARGETS = ["8913601524", "-1003992449851"] 

CHECK_INTERVAL = 25 
# ===================

app = Flask(__name__)

@app.route('/')
def home():
    return "BTS Ticket Bot is running!", 200

last_available_areas = set()
reported_hours = set() 

def send_telegram_notification(message):
    """同步發送訊息給清單中的所有人與頻道"""
    scraper = cloudscraper.create_scraper()
    for target_id in NOTIFICATION_TARGETS:
        api_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {
            "chat_id": target_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            response = scraper.post(api_url, data=payload, timeout=10)
            if response.status_code != 200:
                print(f"[-] Target {target_id} 發送失敗: {response.text}")
        except Exception as e:
            print(f"[-] 發送至 {target_id} 時發生異常: {e}")

def monitor_loop():
    """核心監控無限迴圈"""
    global last_available_areas, reported_hours
    
    # 強制設定為台北時區，避免 Render 伺服器（預設 UTC）導致回報時間錯亂
    tz_taiwan = zoneinfo.ZoneInfo("Asia/Taipei")
    
    # 啟動時發送測試通知
    send_telegram_notification("🤖 *BTS 11/21 高雄場雙重升級版通知機器人已啟動！*\n定時健康檢查時間：09:00、13:00、17:00、21:00")
    
    while True:
        now = datetime.now(tz_taiwan)
        current_hour_min = now.strftime('%H:%M')
        current_date = now.strftime('%Y-%m-%d')
        
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 正在檢查拓元售票狀態...")
        
        # --- 1. 定時定點平安報告 ---
        report_points = ["09:00", "13:00", "17:00", "21:00"]
        if current_hour_min in report_points:
            report_key = f"{current_date}_{current_hour_min}"
            if report_key not in reported_hours:
                report_msg = f"🟢 *【機器人定時回報】*\n報告！目前台北時間為 {current_hour_min}。\n機器人連線一切正常，正在持續死守 [BTS 高雄場]({TARGET_URL})！👍"
                send_telegram_notification(report_msg)
                reported_hours.add(report_key)
                if len(reported_hours) > 20:
                    reported_hours.clear()
        
        # --- 2. 拓元網頁清票爬蟲 ---
        scraper = cloudscraper.create_scraper()
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://tixcraft.com/'
            }
            response = scraper.get(TARGET_URL, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                elements = soup.find_all('li')
                current_available = []
                
                for el in elements:
                    text = el.get_text()
                    if "區" in text and "已售完" not in text:
                        price_keywords = ["9380", "7980", "6980", "5980", "4980", "3980", "2980", "3490", "2990"]
                        if any(price in text for price in price_keywords):
                            clean
