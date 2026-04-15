import requests
from bs4 import BeautifulSoup
import os

# Ayarlar
TARGET_URL = "https://teamfighttactics.leagueoflegends.com/tr-tr/news/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
LAST_NEWS_FILE = "last_news.txt"
ROLE_ID = "1483254703818276976"
CLUB_LOGO_URL = "https://i.imgur.com/sqOABeG.jpeg"

def get_news_list():
    headers = {"User-Agent": "Mozilla/5.0"}
    news_items = []
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('a', href=True, limit=5)
        
        for card in cards:
            title_element = card.find('h2') or card.select_one('[class*="title"]')
            if title_element:
                title = title_element.get_text().strip()
            else:
                title = card.get_text(separator='|').split('|')[0].strip()

            link = card['href']
            if not link.startswith('http'):
                link = "https://teamfighttactics.leagueoflegends.com" + link
            
            if "/news/" in link or "/game-updates/" in link:
                news_items.append({"title": title, "link": link})
        
        return news_items
    except Exception as e:
        print(f"Hata: {e}")
        return []

def main():
    all_news = get_news_list()
    if not all_news: return

    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, "r") as f:
            last_link = f.read().strip()
    else:
        last_link = ""

    new_items_to_post = []
    for item in all_news:
        if item['link'] == last_link:
            break
        new_items_to_post.append(item)

    if new_items_to_post:
        for news in reversed(new_items_to_post):
            # ESKİ DİZAYN: Haber metni ve linki "content" içine geri alındı (Kutunun dışı).
            payload = {
                "username": "TFT Haber Botu",
                "content": f"📢 **TFT Sayfasında Yeni Bir Güncelleme Var!** <@&{ROLE_ID}>\n\n**{news['title']}**\n{news['link']}",
                "embeds": [
                    {
                        # Renk kodunu Discord'un koyu tema arka planına (#313338) eşitledik.
                        # Böylece o sol taraftaki sarı çizgi "görünmez" hale gelecek.
                        "color": 3224376, 
                        "footer": {
                            "text": "Eskişehir Riot Games Kampüs Elçiliği",
                            "icon_url": CLUB_LOGO_URL
                        }
                    }
                ]
            }
            requests.post(WEBHOOK_URL, json=payload)
            print(f"Gönderildi: {news['title']}")

        with open(LAST_NEWS_FILE, "w") as f:
            f.write(all_news[0]['link'])
    else:
        print("Yeni haber yok.")

if __name__ == "__main__":
    main()
