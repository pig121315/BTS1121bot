import time
import random
import threading
from datetime import datetime
import zoneinfo
import cloudscraper
from bs4 import BeautifulSoup
from flask import Flask

# ===== 參數設定 =====
TARGET_URLS = {
    "11/21 高雄場": "https://tixcraft.com/ticket/area/26_btskns/22763"
}

TG_TOKEN = "8944538900:AAGLVNGa2ZnCQBJII7tbf05Wqv1mg6BbqHg"
NOTIFICATION_TARGETS = ["8913601524", "-1003992449851"] 
# ===================

app = Flask(__name__)

@app.route('/')
def home():
    return "BTS Multi-Ticket Bot is safely running!", 200

last_available_by_url = {name: set() for name in TARGET_URLS}
reported_hours = set() 

def send_telegram_notification(message):
    """同步發送訊息給個人與頻道"""
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
            scraper.post(api_url, data=payload, timeout=10)
        except Exception as e:
            print(f"[-] 發送至 {target_id} 時發生異常: {e}")

def monitor_loop():
    global reported_hours
    tz_taiwan = zoneinfo.ZoneInfo("Asia/Taipei")
    
    send_telegram_notification("🤖 *BTS 11/21 高雄場［結構精準修復版］監控啟動！*\n🔥 已全面修正網頁結構誤判問題，死守清票中！")
    
    while True:
        now = datetime.now(tz_taiwan)
        current_hour_min = now.strftime('%H:%M')
        current_date = now.strftime('%Y-%m-%d')
        
        # 定時回報
        report_points = ["09:00", "13:00", "17:00", "21:00"]
        if current_hour_min in report_points:
            report_key = f"{current_date}_{current_hour_min}"
            if report_key not in reported_hours:
                report_msg = f"🟢 *【機器人定時回報】*\n報告！目前台北時間為 {current_hour_min}。\n機器人修正後運作完美，正持續死守 21 號場次中！"
                send_telegram_notification(report_msg)
                reported_hours.add(report_key)
                if len(reported_hours) > 20:
                    reported_hours.clear()
        
        scraper = cloudscraper.create_scraper()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://tixcraft.com/'
        }
        
        for name, url in TARGET_URLS.items():
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 正在檢查 [{name}] 售票狀態...")
            try:
                response = scraper.get(url, headers=headers, timeout=8)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 【核心修正】拓元區域按鈕是 <a> 標籤，直接抓取所有超連結
                    elements = soup.find_all('a')
                    current_available = []
                    
                    for el in elements:
                        text = el.get_text()
                        
                        # 排除導覽列干擾：必須包含「區」，且排除包含「登入」、「問題」、「最新消息」等字眼
                        if "區" in text and not any(skip in text for skip in ["登入", "問題", "消息", "節目"]):
                            # 關鍵判斷：如果這個區域的文字裡「沒有」出現已售完
                            if "已售完" not in text and "售完" not in text:
                                clean_text = " ".join(text.split())
                                if clean_text: # 確保不是空文字
                                    current_available.append(clean_text)
                                
                    current_set = set(current_available)
                    new_tickets = current_set - last_available_by_url[name]
                    
                    if new_tickets:
                        msg = f"🚨 *【BTS {name} 清票通知】* 🚨\n\n"
                        msg += "偵測到以下區域目前 *有票釋出*，請速度前往搶票：\n"
                        for ticket in new_tickets:
                            msg += f"🔹 `{ticket}`\n"
                        msg += f"\n🔗 [點我立即前往拓元售票網]({url})"
                        
                        send_telegram_notification(msg)
                        print(f"[+] 🔥 {name} 發現清票！已發送通知：{new_tickets}")
                    
                    last_available_by_url[name] = current_set
                else:
                    print(f"[-] {name} 連線異常，狀態碼: {response.status_code}")
            except Exception as e:
                print(f"[-] 檢查 {name} 時發生錯誤: {e}")
            
        # 4 ~ 10 秒隨機延遲
        time.sleep(random.uniform(4, 10))

if __name__ == "__main__":
    t = threading.Thread(target=monitor_loop)
    t.daemon = True
    t.start()
    
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
