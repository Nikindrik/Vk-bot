import requests

# Ваш API ключ
api_key = ""

# URL для текущей погоды
url_current = f"http://api.openweathermap.org/data/2.5/weather?q=Moscow&appid={api_key}&units=metric&lang=ru"

# URL для прогноза погоды на завтра
url_forecast = f"http://api.openweathermap.org/data/2.5/forecast?q=Moscow&appid={api_key}&units=metric&lang=ru"


# Функция для проверки ответа API
def check_response(response):
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.json()}")
    return response.json()

# Получение текущей погоды
response_current = requests.get(url_current)
data_current = check_response(response_current)

# Получение прогноза погоды
response_forecast = requests.get(url_forecast)
data_forecast = check_response(response_forecast)

print(url_forecast)

# Парсинг данных текущей погоды
current_weather = {
    "состояние погоды": data_current['weather'][0]['description'],
    "иконка": data_current['weather'][0]['icon'],
    "температура": data_current['main']['temp'],
    "давление": data_current['main']['pressure'],
    "влажность": data_current['main']['humidity'],
    "сила ветра": data_current['wind']['speed'],
    "направление ветра": data_current['wind']['deg']
}

# Парсинг данных прогноза погоды на завтра
# Берем данные через 24 часа
forecast_weather = None
for forecast in data_forecast['list']:
    if '12:00:00' in forecast['dt_txt']:
        forecast_weather = {
            "состояние погоды": forecast['weather'][0]['description'],
            "иконка": forecast['weather'][0]['icon'],
            "температура": forecast['main']['temp'],
            "давление": forecast['main']['pressure'],
            "влажность": forecast['main']['humidity'],
            "сила ветра": forecast['wind']['speed'],
            "направление ветра": forecast['wind']['deg']
        }
        break
import requests

# Ваш API ключ
api_key = "99d0df183eeea6638a2d95070a0bb5a4"


def check_response(response):
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.json()}")
    return response.json()


def get_weather():
    # URL для текущей погоды
    url_current = f"http://api.openweathermap.org/data/2.5/weather?q=Moscow&appid={api_key}&units=metric&lang=ru"

    # URL для прогноза погоды на завтра
    url_forecast = f"http://api.openweathermap.org/data/2.5/forecast?q=Moscow&appid={api_key}&units=metric&lang=ru"

    # Получение текущей погоды
    response_current = requests.get(url_current)
    data_current = check_response(response_current)

    # Получение прогноза погоды
    response_forecast = requests.get(url_forecast)
    data_forecast = check_response(response_forecast)

    return data_current, data_forecast


def format_weather(data, forecast_type):
    if forecast_type == "current":
        weather = {
            "состояние погоды": data['weather'][0]['description'],
            "температура": data['main']['temp'],
            "давление": data['main']['pressure'],
            "влажность": data['main']['humidity'],
            "сила ветра": data['wind']['speed'],
            "направление ветра": data['wind']['deg']
        }
    elif forecast_type == "forecast":
        weather = {
            "состояние погоды": data['weather'][0]['description'],
            "температура": data['main']['temp'],
            "давление": data['main']['pressure'],
            "влажность": data['main']['humidity'],
            "сила ветра": data['wind']['speed'],
            "направление ветра": data['wind']['deg']
        }

    # Конвертация давления из hPa в мм рт. ст.
    weather["давление"] = weather["давление"] * 0.750062
    return weather


def convert_pressure(hpa):
    return hpa * 0.750062


def weather_to_str(weather):
    return (f"Состояние погоды: {weather['состояние погоды']}\n"
            f"Температура: {weather['температура']}°C\n"
            f"Давление: {convert_pressure(weather['давление']):.2f} мм рт. ст.\n"
            f"Влажность: {weather['влажность']}%\n"
            f"Ветер: {weather['сила ветра']} м/с, направление {weather['направление ветра']}°")


current_weather["давление"] = convert_pressure(current_weather["давление"])
if forecast_weather:
    forecast_weather["давление"] = convert_pressure(forecast_weather["давление"])

# Вывод информации
print("Погода в Москве на сегодня:")
print(current_weather)
if forecast_weather:
    print("\nПогода в Москве на завтра:")
    print(forecast_weather)
else:
    print("\nПрогноз погоды на завтра не найден.")