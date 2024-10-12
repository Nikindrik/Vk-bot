import os
import requests
from bs4 import BeautifulSoup

# URL страницы с расписанием
url = 'https://www.mirea.ru/schedule/'

# Папка для сохранения расписания
download_folder = 'schedules'

# Создаем папку, если ее нет
os.makedirs(download_folder, exist_ok=True)

# Получаем HTML-код страницы
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Ищем все ссылки, содержащие "IIT" в href
schedule_links = soup.select('a[href*="IIT"]')

# Берем первые 3 ссылки
first_three_links = schedule_links[:3]

# Проходимся по первым трем найденным ссылкам и скачиваем файлы
for link in first_three_links:
    file_url = link.get('href')
    file_name = os.path.basename(file_url)
    file_path = os.path.join(download_folder, file_name)

    # Скачиваем файл
    file_response = requests.get(file_url)
    with open(file_path, 'wb') as file:
        file.write(file_response.content)

    print(f'Скачан файл: {file_name}')

print('Загрузка первых трех расписаний завершена.')