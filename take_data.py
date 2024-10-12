import glob
from datetime import datetime, timedelta
import pandas as pd


def clean_string(s):
    """ Удаляет переносы строк и заменяет их на чёрточки """
    if isinstance(s, str):
        return s.replace("\n", "\\")
    return s


def get_schedule_for_group(file_paths, group_name, weekday, even_week):
    group_name = group_name.lower()
    schedule_list = []

    for file_path in file_paths:
        df = pd.read_excel(file_path, header=None)
        col_index = None

        # Поиск колонки с нужной группой
        for col in df.columns:
            if group_name in str(df.at[1, col]).lower():
                col_index = col
                break

        if col_index is None:
            continue

        if weekday == 6:
            print('Пар нет')
            return []

        # Вычислить начальную строку для текущего дня недели
        start_row = 3 + weekday * 14
        days_of_week = {
            0: 'понедельник',
            1: 'вторник',
            2: 'среда',
            3: 'четверг',
            4: 'пятница',
            5: 'суббота',
        }
        day_name = days_of_week.get(weekday)
        schedule_list.append(f"Расписание на {day_name} (Четная неделя: {even_week})")

        for i in range(7):
            # Если четная неделя, начинаем с 5-й строки, иначе с 4-й
            row = start_row + i * 2 + (1 if even_week else 0)

            # Проверка наличия данных в строке
            if row < len(df):
                class_name = clean_string(df.at[row, col_index]) if pd.notna(df.at[row, col_index]) else "-"
                class_type = clean_string(df.at[row, col_index + 1]) if pd.notna(df.at[row, col_index + 1]) else "-"
                teacher = clean_string(df.at[row, col_index + 2]) if pd.notna(df.at[row, col_index + 2]) else "-"
                classroom = clean_string(df.at[row, col_index + 3]) if pd.notna(df.at[row, col_index + 3]) else "-"
            else:
                class_name = class_type = teacher = classroom = "-"

            if class_name != '-':
                schedule_list.append(f"{i + 1}) |{class_name}| |{class_type}| |{teacher}| |{classroom}|")
            else:
                schedule_list.append(f"{i + 1}) -")

        break

    if not schedule_list:
        print(f"Группа {group_name} не найдена.")

    return schedule_list


def get_week_evenness(date):
    # Определяем четность недели и меняем на противоположное
    week_number = date.isocalendar()[1]
    return week_number % 2 != 0  # Меняем четность на противоположное


def get_weekday_and_evenness(day_offset=0):
    # Определяем день недели и четность недели с учетом сдвига дней
    target_date = datetime.now() + timedelta(days=day_offset)
    weekday = target_date.weekday()
    even_week = get_week_evenness(target_date)
    return weekday, even_week


def get_week_schedule(file_paths, group_name, start_day_offset):
    # Получаем дату начала недели и её четность
    start_date = datetime.now() + timedelta(days=start_day_offset)
    start_date = start_date - timedelta(days=start_date.weekday())
    even_week = get_week_evenness(start_date)
    print(f"Дата начала недели: {start_date}, Четная неделя: {even_week}")

    week_result = []

    # Вызываем функцию для каждого дня с понедельника по субботу
    for i in range(6):
        weekday = (start_date + timedelta(days=i)).weekday()
        day_result = get_schedule_for_group(file_paths, group_name, weekday, even_week)
        week_result.append(day_result)

    return week_result


def schedule_prompt(file_paths, group_name='икбо-74-23'):
    print("Выберите опцию:")
    print("1 - Сегодня")
    print("2 - Завтра")
    print("3 - Эта неделя")
    print("4 - Следующая неделя")

    choice = int(input("Введите ваш выбор: "))

    if choice == 1:
        # Сегодня
        weekday, even_week = get_weekday_and_evenness()
        result = get_schedule_for_group(file_paths, group_name, weekday, even_week)
        for i in result:
            print(i)
    elif choice == 2:
        # Завтра
        weekday, even_week = get_weekday_and_evenness(day_offset=1)
        result = get_schedule_for_group(file_paths, group_name, weekday, even_week)
        for i in result:
            print(i)
    elif choice == 3:
        # Эта неделя
        result = get_week_schedule(file_paths, group_name, start_day_offset=0)
        for day_result in result:
            for item in day_result:
                print(item)
            print()
    elif choice == 4:
        # Следующая неделя
        result = get_week_schedule(file_paths, group_name, start_day_offset=7)
        for day_result in result:
            for item in day_result:
                print(item)
            print()
    else:
        print("Неверный выбор.")
        return


def load_schedules():
    # Поиск файлов с префиксами "IIT_1-kurs", "IIT_2-kurs" и "IIT_3-kurs" и расширением "xlsx"
    files = glob.glob('schedules/IIT_[1-3]-kurs*.xlsx')
    if not files:
        print("Файлы с расписанием не найдены.")
        return []
    return files


if __name__ == "__main__":
    files = load_schedules()
    if files:
        schedule_prompt(files)