import time
import cloudscraper
from bs4 import BeautifulSoup

# ===== 參數設定（已帶入你的 Telegram 資訊） =====
TARGET_URL = "https://tixcraft.com/ticket/area/26_btskns/22763"
TG_TOKEN = "8944538900:AAGLVNGa2ZnCQBJII7tbf05Wqv1mg6BbqHg"
TG_CHAT_ID = "8913601524"

# 檢查頻率（單位：秒）
# Render 免費版建議設 20~30 秒，避免被拓元短時間內封鎖 IP
CHECK_INTERVAL = 25 
# ===============================================

# 紀錄上一次有票的區域，避免重複通知轟炸
last_available_areas = set()

def send_telegram_notification(message):
    """透過 Telegram Bot 發送通知"""
    api_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.post(api_url, data=payload, timeout=10)
        if response.status_code != 200:
            print(f"[-] Telegram 發送失敗: {response.text}")
    except Exception as e:
        print(f"[-] 發送通知時發生異常: {e}")

def check_tickets():
    global last_available_areas
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] 正在檢查 [BTS 高雄場] 售票狀態...")
    
    scraper = cloudscraper.create_scraper()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://tixcraft.com/'
        }
        
        response = scraper.get(TARGET_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"[-] 網頁連線異常，狀態碼: {response.status_code} (可能遭防爬蟲阻擋)")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 依據拓元網頁結構，尋找所有列表項目
        elements = soup.find_all('li')
        current_available = []
        
        for el in elements:
            text = el.get_text()
            
            # 關鍵過濾邏輯：含有「區」，且「沒有」出現已售完
            if "區" in text and "已售完" not in text:
                # 確保是包含票價的座位區域，排除無關雜訊
                price_keywords = ["9380", "7980", "6980", "5980", "4980", "3980", "2980", "3490", "2990"]
                if any(price in text for price in price_keywords):
                    clean_text = " ".join(text.split())
                    current_available.append(clean_text)
                    
        current_set = set(current_available)
        
        # 比對出新釋出的區域
        new_tickets = current_set - last_available_areas
        
        if new_tickets:
            msg = "🚨 *【BTS 高雄場 清票通知】* 🚨\n\n"
            msg += "偵測到以下區域目前 *有票釋出*，請速度前往搶票：\n"
            for ticket in new_tickets:
                msg += f"🔹 `{ticket}`\n"
            msg += f"\n🔗 [點我立即前往拓元售票網]({TARGET_URL})"
            
            send_telegram_notification(msg)
            print(f"[+] 🔥 發現清票！已發送通知：{new_tickets}")
            
        last_available_areas = current_set

    except Exception as e:
        print(f"[-] 執行檢查時發生錯誤: {e}")

if __name__ == "__main__":
    start_msg = "🤖 *BTS 11/21 高雄場清票監控機器人已啟動！*\n將持續在 Render 雲端環境為您偵測..."
    send_telegram_notification(start_msg)
    
    while True:
        check_tickets()
        time.sleep(CHECK_INTERVAL)
