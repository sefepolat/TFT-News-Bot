import requests
from bs4 import BeautifulSoup
import os

# Ayarlar
TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
LAST_NEWS_FILE = "last_news.txt"
ROLE_ID = "1483254703818276976"

def get_news_list():
    headers = {"User-Agent": "Mozilla/5.0"}
    news_items = []
    try:
        response = requests.get(TARGET_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sayfadaki tüm linkleri bul
        all_links = soup.find_all('a', href=True)
        print(f"DEBUG: Sayfada toplam {len(all_links)} link bulundu.")
        
        for card in all_links:
            link = card['href']
            if not link.startswith('http'):
                link = "https://teamfighttactics.leagueoflegends.com" + link
            
            # Sadece gerçek haber linklerini al ve linki temizle (sonundaki / işaretini sil)
            clean_link = link.strip().rstrip('/')
            
            if "/news/" in clean_link or "/game-updates/" in clean_link:
                title_element = card.find(['h2', 'h3']) or card.select_one('[class*="title"]')
                title = title_element.get_text().strip() if title_element else "TFT Duyurusu"
                
                # Tekrar eden linkleri engelle
                if not any(item['link'] == clean_link for item in news_items):
                    news_items.append({"title": title, "link": clean_link})
        
        print(f"DEBUG: Toplam {len(news_items)} geçerli haber linki ayıklandı.")
        return news_items
    except Exception as e:
        print(f"HATA (Scraping): {e}")
        return []

def main():
    all_news = get_news_list()
    if not all_news:
        print("HATA: Hiç haber bulunamadı!")
        return

    # Dosyadaki son linki oku ve temizle
    last_link = ""
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_link = f.read().strip().rstrip('/')
    
    print(f"DEBUG: Veritabanındaki (txt) son link: '{last_link}'")

    # Yeni haberleri bul
    new_items_to_post = []
    for item in all_news:
        if item['link'] == last_link:
            print(f"DEBUG: '{item['link']}' linkine ulaşıldı, daha eskilere bakılmıyor.")
            break
        new_items_to_post.append(item)

    if new_items_to_post:
        print(f"DEBUG: {len(new_items_to_post)} adet YENİ haber gönderiliyor...")
        
        # Eskiden yeniye sırala ve gönder
        for news in reversed(new_items_to_post):
            payload = {
                "username": "TFT Haber Botu",
                "content": f"📢 **TFT Sayfasında Yeni Bir Güncelleme Var!** <@&{ROLE_ID}>\n\n**{news['title']}**\n{news['link']}"
            }
            res = requests.post(WEBHOOK_URL, json=payload)
            print(f"DEBUG: Gönderildi: {news['title']} (Durum Kodu: {res.status_code})")

        # EN YENİ haberi dosyaya kaydet
        with open(LAST_NEWS_FILE, "w") as f:
            f.write(all_news[0]['link'])
        print(f"DEBUG: {LAST_NEWS_FILE} güncellendi: {all_news[0]['link']}")
    else:
        print("DURUM: Yeni haber yok, her şey güncel.")

if __name__ == "__main__":
    main()
