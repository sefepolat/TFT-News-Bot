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
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # .find() yerine .find_all() kullanarak ilk 10 linki alıyoruz
        # Sadece içinde /news/ veya /game-updates/ geçen linkleri filtreliyoruz
        all_links = soup.find_all('a', href=True)
        
        for card in all_links:
            link = card['href']
            if not link.startswith('http'):
                link = "https://teamfighttactics.leagueoflegends.com" + link
            
            # Gerçek bir haber linki mi kontrol et ve listeye ekle
            if "/news/" in link or "/game-updates/" in link:
                # Başlık bulma mantığın (dokunmadım)
                title_element = card.find('h2') or card.select_one('[class*="title"]')
                if title_element:
                    title = title_element.get_text().strip()
                else:
                    title = card.get_text(separator='|').split('|')[0].strip()
                
                # Listeye ekle (Eğer zaten eklenmediyse - bazen aynı link 2 kere olabilir)
                if not any(item['link'] == link for item in news_items):
                    news_items.append({"title": title, "link": link})
            
            # İlk 10 geçerli haber linkini bulduğumuzda durabiliriz
            if len(news_items) >= 10: break
            
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

    # Yeni haberleri tespit et
    new_items_to_post = []
    for item in all_news:
        if item['link'] == last_link:
            break # En son paylaştığımız habere geldik, döngüyü kır.
        new_items_to_post.append(item)

    if new_items_to_post:
        # En eskiden en yeniye doğru gönderiyoruz (Ters sıra)
        for news in reversed(new_items_to_post):
            payload = {
                "username": "TFT Haber Botu",
                "content": f"📢 **TFT Sayfasında Yeni Bir Güncelleme Var!** <@&{ROLE_ID}>\n\n**{news['title']}**\n{news['link']}"
            }
            requests.post(WEBHOOK_URL, json=payload)
            print(f"Gönderildi: {news['title']}")

        # Dosyayı sayfadaki EN YENİ (ilk) haberle güncelle
        with open(LAST_NEWS_FILE, "w") as f:
            f.write(all_news[0]['link'])
    else:
        print("Yeni haber yok.")

if __name__ == "__main__":
    main()
