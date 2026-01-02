import os
import json
import sys
from datetime import datetime, timedelta, timezone
import requests
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

def get_news_kyrgyzstan():
    rss_url = config.get("rss_url", "https://kaktus.media/?rss")
    try:
        response = requests.get(rss_url)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print("Не удалось получить RSS фид.")
            return
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        print(f"Items found: {len(items)}")
        if not items:
            print("Новости не найдены.")
            return
        now = datetime.now(timezone.utc)
        three_days_ago = now - timedelta(days=3)
        recent_news = []
        for item in items:
            pubdate_elem = item.find('pubDate')
            if pubdate_elem is not None:
                try:
                    pubdate_str = pubdate_elem.text
                    pubdate = datetime.strptime(pubdate_str, "%a, %d %b %Y %H:%M:%S %z")
                    if pubdate > three_days_ago:
                        title_elem = item.find('title')
                        title = title_elem.text if title_elem is not None else 'Без заголовка'
                        link_elem = item.find('link')
                        url = link_elem.text if link_elem is not None else ''
                        recent_news.append(f"{title}\n{url}")
                except ValueError:
                    continue
            if len(recent_news) >= 5:
                break
        if not recent_news:
            print("Нет новостей за последние 3 дня.")
            return
        for i, news in enumerate(recent_news, 1):
            print(f"{i}. {news}\n")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    get_news_kyrgyzstan()