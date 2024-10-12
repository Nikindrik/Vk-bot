import requests
import time
import json
import pandas as pd
import glob
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
import find_lessons_teacher as flt  # Импортируем функции из вашего файла
import take_data

# Ваш access_token
ACCESS_TOKEN = 'vk1.a.z6vnokfkRGoCSPZbWHgjbXcSfz3BnEobllAwIt7T5iKwxRAWCK7pkgcFrQ_5VZwDslU4Hcvqs1y_21A20s1byFiBC1leZ4pKzSvSIPuCG4VRaK02goy8-T1OLG832s9gRb6rOpJeJjQ-IKbqPdYevYThY4cHbrZ0hBGlHfw9OCSW0_JG2RkZqwD2lropjLwRCc8i_aaWBFXmuPtnRzeT6A'
GROUP_ID = '225958504'
API_VERSION = '5.236'

USER_GROUP_FILE = 'user_groups.json'
USER_STATES = {}

DAYS_OF_WEEK = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

# Функции для работы с погодой

# Ваш API ключ
api_key = ""


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
            "направление ветра": data['wind']['deg'],
            "иконка": data['weather'][0]['icon']
        }
    elif forecast_type == "forecast":
        weather = {
            "состояние погоды": data['weather'][0]['description'],
            "температура": data['main']['temp'],
            "давление": data['main']['pressure'],
            "влажность": data['main']['humidity'],
            "сила ветра": data['wind']['speed'],
            "направление ветра": data['wind']['deg'],
            "иконка": data['weather'][0]['icon']
        }

    # Конвертация давления из hPa в мм рт. ст.
    weather["давление"] = weather["давление"] * 0.750062
    return weather


def weather_to_str(weather):
    return (f"Состояние погоды: {weather['состояние погоды']}\n"
            f"Температура: {weather['температура']}°C\n"
            f"Давление: {weather['давление']:.2f} мм рт. ст.\n"
            f"Влажность: {weather['влажность']}%\n"
            f"Ветер: {weather['сила ветра']} м/с, направление {weather['направление ветра']}°")


def get_icon_url(icon_id):
    return f"http://openweathermap.org/img/wn/{icon_id}@2x.png"


def create_image_row(icon_ids):
    images = [Image.open(BytesIO(requests.get(get_icon_url(icon_id)).content)) for icon_id in icon_ids]
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGBA', (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.width

    return new_im


def send_image(peer_id, image):
    # Сохраним изображение в BytesIO
    image_io = BytesIO()
    image.save(image_io, format='PNG')
    image_io.seek(0)

    # Загружаем изображение на сервер VK
    upload_url = requests.get(
        f'https://api.vk.com/method/photos.getMessagesUploadServer?access_token={ACCESS_TOKEN}&v={API_VERSION}&peer_id={peer_id}').json()[
        'response']['upload_url']
    response = requests.post(upload_url, files={'photo': ('image.png', image_io, 'image/png')}).json()

    # Сохраняем фото
    save_response = requests.get(
        f"https://api.vk.com/method/photos.saveMessagesPhoto?access_token={ACCESS_TOKEN}&v={API_VERSION}&server={response['server']}&photo={response['photo']}&hash={response['hash']}"
    ).json()

    # Отправляем фото
    photo = save_response['response'][0]
    media_id = f"photo{photo['owner_id']}_{photo['id']}"
    params = {
        'access_token': ACCESS_TOKEN,
        'v': API_VERSION,
        'peer_id': peer_id,
        'attachment': media_id,
        'random_id': 0
    }
    requests.post('https://api.vk.com/method/messages.send', params=params)


def handle_weather_choice(peer_id, text):
    data_current, data_forecast = get_weather()
    if text == "current_weather":
        current_weather = format_weather(data_current, "current")
        icon_url = get_icon_url(data_current['weather'][0]['icon'])
        image = Image.open(BytesIO(requests.get(icon_url).content))
        send_image(peer_id, image)
        send_message(peer_id, weather_to_str(current_weather), weather_keyboard)
    elif text == "today_weather":
        send_message(peer_id, "Погода на сегодня:", weather_keyboard)
        send_day_forecast(peer_id, data_forecast, 0, include_all_periods=True)
    elif text == "tomorrow_weather":
        send_message(peer_id, "Погода на завтра:", weather_keyboard)
        send_day_forecast(peer_id, data_forecast, 1, include_all_periods=True)
    elif text == "five_days_weather":
        day_temps = []
        night_temps = []
        day_icons = []
        night_icons = []
        for day_offset in range(5):
            date = (datetime.now() + timedelta(days=day_offset)).date()
            day_temp = None
            night_temp = None
            day_icon = None
            night_icon = None
            for forecast in data_forecast['list']:
                forecast_date = datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S').date()
                if forecast_date == date:
                    if "12:00:00" in forecast['dt_txt']:
                        day_temp = format_weather(forecast, "forecast")['температура']
                        day_icon = forecast['weather'][0]['icon']
                    elif "00:00:00" in forecast['dt_txt']:
                        night_temp = format_weather(forecast, "forecast")['температура']
                        night_icon = forecast['weather'][0]['icon']
            day_temps.append(f"{day_temp}°C" if day_temp is not None else "N/A")
            night_temps.append(f"{night_temp}°C" if night_temp is not None else "N/A")
            day_icons.append(day_icon)
            night_icons.append(night_icon)
        day_forecast_str = "|".join(day_temps) + " | День"
        night_forecast_str = "|".join(night_temps) + " | Ночь"
        full_forecast_str = f"{day_forecast_str}\n{night_forecast_str}"

        # Создание изображения с иконками
        day_image = create_image_row(day_icons)
        night_image = create_image_row(night_icons)

        # Отправка изображений
        send_image(peer_id, day_image)
        send_image(peer_id, night_image)

        send_message(peer_id, full_forecast_str, weather_keyboard)
    USER_STATES[peer_id] = None


def send_day_forecast(peer_id, data_forecast, day_offset, include_all_periods=False):
    periods = {
        "Утро": "06:00:00",
        "День": "12:00:00",
        "Вечер": "18:00:00",
        "Ночь": "00:00:00"
    } if include_all_periods else {
        "День": "12:00:00",
        "Ночь": "00:00:00"
    }
    date = (datetime.now() + timedelta(days=day_offset)).date()
    forecast_str = f"Прогноз на {date.strftime('%d.%m.%Y')}:\n"
    icon_ids = []
    for period_name, period_time in periods.items():
        forecast_weather = None
        for forecast in data_forecast['list']:
            forecast_date = datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S').date()
            if forecast_date == date and period_time in forecast['dt_txt']:
                forecast_weather = format_weather(forecast, "forecast")
                icon_ids.append(forecast_weather['иконка'])
                break
        if forecast_weather:
            forecast_str += f"\n{period_name}:\n{weather_to_str(forecast_weather)}\n"
        else:
            forecast_str += f"\n{period_name}:\nПрогноз не найден\n"
    image = create_image_row(icon_ids)
    send_image(peer_id, image)
    send_message(peer_id, forecast_str, weather_keyboard)


# Функции бота

def get_long_poll_server():
    url = f'https://api.vk.com/method/groups.getLongPollServer'
    params = {
        'group_id': GROUP_ID,
        'access_token': ACCESS_TOKEN,
        'v': API_VERSION
    }
    response = requests.get(url, params=params)
    data = response.json()
    print("Long Poll Server data:", data)
    return data['response']


def listen_to_events(server, key, ts):
    url = f'{server}?act=a_check&key={key}&ts={ts}&wait=25'
    response = requests.get(url).json()
    print("Listen to events response:", response)
    return response


def send_message(peer_id, message, keyboard=None):
    if not message:
        message = "Что хотите сделать?" if keyboard == action_keyboard else "Выберите действие:"

    url = 'https://api.vk.com/method/messages.send'
    params = {
        'access_token': ACCESS_TOKEN,
        'v': API_VERSION,
        'peer_id': peer_id,
        'message': message,
        'random_id': 0
    }
    if keyboard:
        params['keyboard'] = json.dumps(keyboard)

    try:
        response = requests.post(url, params=params)
        response_data = response.json()
        print("Send message response:", response_data)
        if 'error' in response_data:
            print("Error sending message:", response_data['error'])
        return response_data
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        print("Response content:", response.content)
    except Exception as e:
        print("Error sending message:", e)


def load_user_groups():
    try:
        with open(USER_GROUP_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_user_group(user_id, group_name):
    user_groups = load_user_groups()
    user_groups[str(user_id)] = group_name
    with open(USER_GROUP_FILE, 'w') as file:
        json.dump(user_groups, file, ensure_ascii=False, indent=4)


def handle_start(peer_id, user_groups):
    peer_id_str = str(peer_id)
    if peer_id_str in user_groups:
        group_name = user_groups[peer_id_str]
        send_message(peer_id, f"Ваша сохраненная группа: {group_name}. Что хотите сделать?", action_keyboard)
    else:
        send_message(peer_id, "Введите номер группы:")
        USER_STATES[peer_id] = "awaiting_group"


def handle_group_input(peer_id, text):
    group_name = text
    files = flt.load_schedules()
    group_found = False
    for file in files:
        if get_schedule_for_group(file, group_name):
            group_found = True
            save_user_group(peer_id, group_name)
            send_message(peer_id, f"Группа {group_name} найдена и сохранена. Что хотите сделать?", action_keyboard)
            USER_STATES[peer_id] = None
            break
    if not group_found:
        send_message(peer_id, f"Группа {group_name} не найдена. Пожалуйста, попробуйте снова.")


def get_schedule_for_group(file_path, group_name):
    df = pd.read_excel(file_path, header=None)
    group_name = group_name.lower()

    # Поиск колонки с нужной группой
    for col in df.columns:
        if group_name in str(df.at[1, col]).lower():
            return True

    print(f"Группа {group_name} не найдена в файле {file_path}.")
    return False


def handle_teacher_surname_input(peer_id, text):
    surname = text
    files = flt.load_schedules()
    teachers = flt.search_teachers_in_files(files, surname)
    if not teachers:
        send_message(peer_id, "Преподаватель не найден. Пожалуйста, попробуйте снова.")
        USER_STATES[peer_id] = "awaiting_teacher_surname"
    elif len(teachers) > 1:
        buttons = [[{
            "action": {
                "type": "text",
                "payload": f"{{\"button\": \"teacher_{i}\"}}",
                "label": teacher
            },
            "color": "primary"
        }] for i, teacher in enumerate(teachers, start=1)]
        teacher_choice_keyboard = {
            "one_time": True,
            "buttons": buttons
        }
        send_message(peer_id, "Найдено несколько преподавателей. Выберите нужного:", teacher_choice_keyboard)
        USER_STATES[peer_id] = "choosing_teacher"
        USER_STATES[f'{peer_id}_teachers'] = teachers
        print(f"Teachers saved for user {peer_id}: {teachers}")
    else:
        USER_STATES[peer_id] = f"found_teacher_{teachers[0]}"
        send_message(peer_id, f"Преподаватель {teachers[0]} найден. Выберите период:", period_keyboard)


def handle_teacher_choice(peer_id, teacher_index):
    try:
        teacher = USER_STATES[f'{peer_id}_teachers'][teacher_index]
        USER_STATES[peer_id] = f"found_teacher_{teacher}"
        send_message(peer_id, f"Преподаватель {teacher} найден. Выберите период:", period_keyboard)
    except KeyError as e:
        print(f"KeyError: {e}")
        send_message(peer_id, "Произошла ошибка при выборе преподавателя. Пожалуйста, попробуйте снова.", action_keyboard)
    except IndexError as e:
        print(f"IndexError: {e}")
        send_message(peer_id, "Произошла ошибка при выборе преподавателя. Пожалуйста, попробуйте снова.", action_keyboard)
    except Exception as e:
        print(f"Exception: {e}")
        send_message(peer_id, "Произошла ошибка при выборе преподавателя. Пожалуйста, попробуйте снова.", action_keyboard)


def handle_period_choice(peer_id, text):
    teacher = USER_STATES[peer_id].split('_')[-1]
    period = text
    files = flt.load_schedules()
    try:
        if period == "today":
            day = datetime.now().isoweekday()
            parity = flt.determine_parity()
            schedule = flt.find_teacher_schedule_in_files(files, day, parity, teacher)
            response_message = f"Расписание преподавателя {teacher} на сегодня ({DAYS_OF_WEEK[day - 1]}):\n" + format_schedule(schedule)
            send_message(peer_id, response_message, action_keyboard)
        elif period == "tomorrow":
            day = (datetime.now() + timedelta(days=1)).isoweekday()
            parity = flt.determine_parity()
            schedule = flt.find_teacher_schedule_in_files(files, day, parity, teacher)
            response_message = f"Расписание преподавателя {teacher} на завтра ({DAYS_OF_WEEK[day - 1]}):\n" + format_schedule(schedule)
            send_message(peer_id, response_message, action_keyboard)
        elif period == "this_week":
            send_week_schedule(peer_id, files, teacher, 0)
        elif period == "next_week":
            send_week_schedule(peer_id, files, teacher, 1)
    except Exception as e:
        print(f'Error: {e}')
        send_message(peer_id, "Произошла ошибка при получении расписания. Пожалуйста, попробуйте снова.", action_keyboard)


def send_week_schedule(peer_id, files, teacher, week_offset):
    days = list(range(1, 7))
    parity = flt.determine_parity(week_offset)
    week_schedule = f"Расписание преподавателя {teacher} на {'следующую' if week_offset else 'эту'} неделю:\n"
    for day in days:
        schedule = flt.find_teacher_schedule_in_files(files, day, parity, teacher)
        day_schedule = f"{DAYS_OF_WEEK[day - 1]}:\n" + format_schedule(schedule)
        send_message(peer_id, day_schedule)
        time.sleep(1)  # Задержка в одну секунду между сообщениями
    send_message(peer_id, "Что хотите сделать дальше?", action_keyboard)


def format_schedule(schedule):
    result = ""
    for pair_number, details in schedule.items():
        result += f"Пара №{pair_number}:\n"
        if details['groups'] or details['class_names'] or details['class_types'] or details['classrooms']:
            groups_str = " | ".join(details['groups'])
            class_names_str = " | ".join(details['class_names'])
            class_types_str = " | ".join(details['class_types'])
            classrooms_str = " | ".join(details['classrooms'])
            result += f"  Группа: {groups_str}, Название пары: {class_names_str}, Вид занятий: {class_types_str}, Аудитория: {classrooms_str}\n"
        else:
            result += "  -\n"
    return result


def handle_group_schedule_request(peer_id):
    period_keyboard = {
        "one_time": True,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"group_today\"}",
                    "label": "На сегодня"
                },
                "color": "positive"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"group_tomorrow\"}",
                    "label": "На завтра"
                },
                "color": "negative"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"group_this_week\"}",
                    "label": "На эту неделю"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"group_next_week\"}",
                    "label": "На следующую неделю"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"group_name\"}",
                    "label": "Какая группа?"
                },
                "color": "secondary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"week_parity\"}",
                    "label": "Какая неделя?"
                },
                "color": "secondary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"back_to_main\"}",
                    "label": "Назад к выбору основных функций"
                },
                "color": "secondary"
            }]
        ]
    }
    send_message(peer_id, "Выберите период:", period_keyboard)
    USER_STATES[peer_id] = "awaiting_group_schedule_choice"

def handle_group_schedule_choice(peer_id, choice):
    user_groups = load_user_groups()
    group_name = user_groups.get(str(peer_id))

    if not group_name and choice not in ["group_name", "week_parity"]:
        send_message(peer_id, "Группа не найдена. Пожалуйста, введите номер группы.")
        USER_STATES[peer_id] = "awaiting_group"
        return

    files = flt.load_schedules()
    schedule = []

    if choice == "group_today":
        weekday, even_week = take_data.get_weekday_and_evenness()
        schedule = take_data.get_schedule_for_group(files, group_name, weekday, even_week)
        schedule_str = "\n".join(schedule)
        send_message(peer_id, schedule_str, action_keyboard)
    elif choice == "group_tomorrow":
        weekday, even_week = take_data.get_weekday_and_evenness(day_offset=1)
        schedule = take_data.get_schedule_for_group(files, group_name, weekday, even_week)
        schedule_str = "\n".join(schedule)
        send_message(peer_id, schedule_str, action_keyboard)
    elif choice == "group_this_week":
        schedule = take_data.get_week_schedule(files, group_name, start_day_offset=0)
        for day_schedule in schedule:
            schedule_str = "\n".join(day_schedule)
            send_message(peer_id, schedule_str)
            time.sleep(1)  # Задержка в одну секунду между сообщениями
        send_message(peer_id, "Что хотите сделать дальше?", action_keyboard)
    elif choice == "group_next_week":
        schedule = take_data.get_week_schedule(files, group_name, start_day_offset=7)
        for day_schedule in schedule:
            schedule_str = "\n".join(day_schedule)
            send_message(peer_id, schedule_str)
            time.sleep(1)  # Задержка в одну секунду между сообщениями
        send_message(peer_id, "Что хотите сделать дальше?", action_keyboard)
    elif choice == "group_name":
        send_message(peer_id, f"Ваша группа: {group_name}", action_keyboard)
    elif choice == "week_parity":
        even_week = take_data.get_week_evenness(datetime.now())
        week_parity = "Четная неделя" if even_week else "Нечетная неделя"
        send_message(peer_id, f"Сейчас {week_parity}.", action_keyboard)
    else:
        send_message(peer_id, "Неверный выбор. Пожалуйста, выберите снова.", period_keyboard)
        return

    USER_STATES[peer_id] = None


def handle_message_new(peer_id, text, payload=None):
    user_groups = load_user_groups()
    if peer_id not in USER_STATES:
        USER_STATES[peer_id] = None

    if payload:
        if payload.get("button") == "back_to_main":
            send_message(peer_id, "Что хотите сделать?", action_keyboard)
            USER_STATES[peer_id] = None
            return
        elif payload.get("button") == "teacher_schedule":
            send_message(peer_id, "Напишите фамилию преподавателя:")
            USER_STATES[peer_id] = "awaiting_teacher_surname"
            return
        elif payload.get("button") == "group_schedule":
            handle_group_schedule_request(peer_id)
            return
        elif payload.get("button") == "weather":
            send_message(peer_id, "Выберите период прогноза:", weather_keyboard)
            return
        elif payload.get("button").startswith("teacher_"):
            handle_teacher_choice(peer_id, int(payload.get("button").split('_')[-1]) - 1)
            return
        elif payload.get("button") in ["today", "tomorrow", "this_week", "next_week"]:
            handle_period_choice(peer_id, payload.get("button"))
            return
        elif payload.get("button") in ["current_weather", "today_weather", "tomorrow_weather", "five_days_weather"]:
            handle_weather_choice(peer_id, payload.get("button"))
            return
        elif payload.get("button") in ["group_today", "group_tomorrow", "group_this_week", "group_next_week", "group_name", "week_parity"]:
            handle_group_schedule_choice(peer_id, payload.get("button"))
            return

    if text == "старт":
        handle_start(peer_id, user_groups)
    elif USER_STATES[peer_id] == "awaiting_group":
        handle_group_input(peer_id, text)
    elif USER_STATES[peer_id] == "awaiting_teacher_surname":
        handle_teacher_surname_input(peer_id, text)
    elif USER_STATES[peer_id] and USER_STATES[peer_id].startswith("choosing_teacher"):
        try:
            handle_teacher_choice(peer_id, int(text) - 1)
        except ValueError:
            send_message(peer_id, "Произошла ошибка при выборе преподавателя. Пожалуйста, попробуйте снова.", action_keyboard)
    elif USER_STATES[peer_id] and USER_STATES[peer_id].startswith("found_teacher"):
        handle_period_choice(peer_id, text)
    elif USER_STATES[peer_id] == "awaiting_group_schedule_choice":
        handle_group_schedule_choice(peer_id, text)
    elif text == "узнать расписание преподавателя":
        send_message(peer_id, "Напишите фамилию преподавателя:")
        USER_STATES[peer_id] = "awaiting_teacher_surname"
    elif text == "узнать расписание группы":
        send_message(peer_id, "Введите номер группы:")
        USER_STATES[peer_id] = "awaiting_group"
    elif text == "узнать погоду":
        send_message(peer_id, "Выберите период прогноза:", weather_keyboard)
    else:
        send_message(peer_id, "Нажмите 'Старт' для начала.", start_keyboard)

def main():
    long_poll_data = get_long_poll_server()
    server = long_poll_data['server']
    key = long_poll_data['key']
    ts = long_poll_data['ts']

    while True:
        try:
            response = listen_to_events(server, key, ts)
            if 'failed' in response:
                if response['failed'] == 1:
                    ts = response['ts']
                elif response['failed'] in [2, 3]:
                    long_poll_data = get_long_poll_server()
                    server = long_poll_data['server']
                    key = long_poll_data['key']
                    ts = long_poll_data['ts']
                continue

            ts = response['ts']
            updates = response['updates']
            for update in updates:
                if update['type'] == 'message_new':
                    message = update['object']['message']
                    peer_id = message['peer_id']
                    text = message['text'].strip().lower()
                    payload = json.loads(message.get('payload', '{}'))
                    handle_message_new(peer_id, text, payload)

        except Exception as e:
            print(f'Error: {e}')
            time.sleep(3)  # Ожидание перед повторной попыткой


if __name__ == "__main__":
    # Создаем стартовую клавиатуру с кнопкой "Старт"
    start_keyboard = {
        "one_time": True,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"start\"}",
                    "label": "Старт"
                },
                "color": "primary"
            }]
        ]
    }

    # Создаем клавиатуру для выбора действий
    action_keyboard = {
        "one_time": False,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"teacher_schedule\"}",
                    "label": "Узнать расписание преподавателя"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"group_schedule\"}",
                    "label": "Узнать расписание группы"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"weather\"}",
                    "label": "Узнать погоду"
                },
                "color": "primary"
            }]
        ]
    }

    # Создаем клавиатуру для выбора периода расписания преподавателя
    period_keyboard = {
        "one_time": True,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"today\"}",
                    "label": "На сегодня"
                },
                "color": "positive"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"tomorrow\"}",
                    "label": "На завтра"
                },
                "color": "negative"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"this_week\"}",
                    "label": "На эту неделю"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"next_week\"}",
                    "label": "На следующую неделю"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"back_to_main\"}",
                    "label": "Назад к выбору основных функций"
                },
                "color": "secondary"
            }]
        ]
    }

    # Создаем клавиатуру для выбора периода прогноза погоды
    weather_keyboard = {
        "one_time": True,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"current_weather\"}",
                    "label": "Сейчас"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"today_weather\"}",
                    "label": "На сегодня"
                },
                "color": "positive"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"tomorrow_weather\"}",
                    "label": "На завтра"
                },
                "color": "positive"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"five_days_weather\"}",
                    "label": "На 5 дней"
                },
                "color": "positive"
            }],
            [{
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"back_to_main\"}",
                    "label": "Назад к выбору основных функций"
                },
                "color": "secondary"
            }]
        ]
    }

    main()