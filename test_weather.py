import json
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

def get_weather(city):
    # Geocode the city
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru"
    try:
        geo_response = requests.get(geo_url)
        print(f"Geo status: {geo_response.status_code}")
        if geo_response.status_code != 200:
            print("Не удалось найти город.")
            return
        geo_data = geo_response.json()
        if 'results' not in geo_data or len(geo_data['results']) == 0:
            print("Город не найден.")
            return
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        print(f"Найден город: {geo_data['results'][0]['name']}, lat: {lat}, lon: {lon}")

        # Get weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        weather_response = requests.get(weather_url)
        print(f"Weather status: {weather_response.status_code}")
        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            temp = weather_data['current_weather']['temperature']
            weathercode = weather_data['current_weather']['weathercode']
            # Decode weathercode to description
            descriptions = {
                0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность", 3: "пасмурно",
                45: "туман", 48: "изморось", 51: "мелкий дождь", 53: "дождь", 55: "сильный дождь",
                56: "ледяной дождь", 57: "сильный ледяной дождь", 61: "небольшой дождь", 63: "дождь", 65: "сильный дождь",
                66: "ледяной дождь", 67: "сильный ледяной дождь", 71: "небольшой снег", 73: "снег", 75: "сильный снег",
                77: "снежные зерна", 80: "небольшой дождь", 81: "дождь", 82: "сильный дождь",
                85: "небольшой снег", 86: "сильный снег", 95: "гроза", 96: "гроза с градом", 99: "сильная гроза с градом"
            }
            description = descriptions.get(weathercode, "неизвестно")
            print(f"Погода в {city}: {temp}°C, {description}")
        else:
            print("Не удалось получить данные о погоде.")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    # Test with Bishkek
    get_weather("Bishkek")