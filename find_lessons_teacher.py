import pandas as pd
from datetime import datetime, timedelta
import glob

def load_schedules():
    # Поиск файлов с префиксами "IIT_1-kurs", "IIT_2-kurs" и "IIT_3-kurs" и расширением "xlsx"
    files = glob.glob('schedules/IIT_[1-3]-kurs*.xlsx')
    if not files:
        print("Файлы с расписанием не найдены.")
        return []
    return files

def get_schedule_for_group(file_path, group_name):
    df = pd.read_excel(file_path, header=None)
    group_name = group_name.lower()
    col_index = None

    # Поиск колонки с нужной группой
    for col in df.columns:
        if group_name in str(df.at[1, col]).lower():
            return True


def search_teachers_in_files(files, surname):
    teachers = set()
    for file_path in files:
        df = pd.read_excel(file_path, header=None)
        for col in range(7, df.shape[1], 15):
            for row in range(df.shape[0]):
                cell_value = df.iloc[row, col]
                if pd.notna(cell_value):
                    cell_value_parts = cell_value.split('\n')
                    for part in cell_value_parts:
                        part = part.strip()
                        if surname.lower() in part.lower():
                            teachers.add(part.split(',')[0].strip())
                if col + 5 < df.shape[1]:
                    cell_value = df.iloc[row, col + 5]
                    if pd.notna(cell_value):
                        cell_value_parts = cell_value.split('\n')
                        for part in cell_value_parts:
                            part = part.strip()
                            if surname.lower() in part.lower():
                                teachers.add(part.split(',')[0].strip())
    return list(teachers)


def get_value_from_cell(cell, position):
    if pd.isna(cell):
        return 'N/A'
    parts = cell.split('\n')
    if position < len(parts):
        return parts[position].strip()
    return parts[0].strip()  # Если нет разделения, возвращаем первую часть


def find_teacher_schedule_in_files(files, day, parity, teacher):
    schedule = {i: {'groups': set(), 'class_names': set(), 'class_types': set(), 'classrooms': set()} for i in
                range(1, 8)}
    for file_path in files:
        df = pd.read_excel(file_path, header=None)
        start_row = 3 + (day - 1) * 14
        rows = list(range(start_row, start_row + 14))
        relevant_rows = rows[::2] if parity == 'even' else rows[1::2]

        for idx, row in enumerate(relevant_rows, start=1):
            for col in range(7, df.shape[1], 15):
                if pd.notna(df.iloc[row, col]):
                    cell_value_parts = df.iloc[row, col].split('\n')
                    for part_idx, part in enumerate(cell_value_parts):
                        part = part.strip()
                        if teacher in part.split(',')[0].strip():
                            group_number = get_value_from_cell(df.iloc[1, col - 2], part_idx) if col - 2 >= 0 else 'N/A'
                            class_name = get_value_from_cell(df.iloc[row, col - 2], part_idx) if col - 2 >= 0 else 'N/A'
                            class_type = get_value_from_cell(df.iloc[row, col - 1], part_idx) if col - 1 >= 0 else 'N/A'
                            classroom = get_value_from_cell(df.iloc[row, col + 1], part_idx) if col + 1 < df.shape[
                                1] else 'N/A'
                            schedule[idx]['groups'].add(group_number)
                            schedule[idx]['class_names'].add(class_name)
                            schedule[idx]['class_types'].add(class_type)
                            schedule[idx]['classrooms'].add(classroom)
                if col + 5 < df.shape[1] and pd.notna(df.iloc[row, col + 5]):
                    cell_value_parts = df.iloc[row, col + 5].split('\n')
                    for part_idx, part in enumerate(cell_value_parts):
                        part = part.strip()
                        if teacher in part.split(',')[0].strip():
                            group_number = get_value_from_cell(df.iloc[1, col + 3], part_idx) if col + 3 < df.shape[
                                1] else 'N/A'
                            class_name = get_value_from_cell(df.iloc[row, col + 3], part_idx) if col + 3 < df.shape[
                                1] else 'N/A'
                            class_type = get_value_from_cell(df.iloc[row, col + 4], part_idx) if col + 4 < df.shape[
                                1] else 'N/A'
                            classroom = get_value_from_cell(df.iloc[row, col + 6], part_idx) if col + 6 < df.shape[
                                1] else 'N/A'
                            schedule[idx]['groups'].add(group_number)
                            schedule[idx]['class_names'].add(class_name)
                            schedule[idx]['class_types'].add(class_type)
                            schedule[idx]['classrooms'].add(classroom)
    return schedule


def determine_parity(week_offset=0):
    # Определение четности недели с учетом смещения
    current_week = datetime.now().isocalendar()[1] + week_offset
    return 'even' if current_week % 2 == 0 else 'odd'

def print_schedule_for_day(schedule, teacher, day):
    result = []
    result.append(f"Расписание пар преподавателя - {teacher} на день {day}:")
    for pair_number, details in schedule.items():
        if details['groups'] or details['class_names'] or details['class_types'] or details['classrooms']:
            groups_str = " | ".join(details['groups'])
            class_names_str = " | ".join(details['class_names'])
            class_types_str = " | ".join(details['class_types'])
            classrooms_str = " | ".join(details['classrooms'])
            result.append(f"Пара №{pair_number}:")
            result.append(f"  Группа: {groups_str}, Название пары: {class_names_str}, Вид занятий: {class_types_str}, Аудитория: {classrooms_str}")
        else:
            result.append(f"Пара №{pair_number}:")
            result.append("  -")
    return "\n".join(result)

def main():
    files = load_schedules()
    if not files:
        return

    options = {
        '1': "Сегодня",
        '2': "Завтра",
        '3': "На эту неделю",
        '4': "На следующую неделю"
    }

    print("Выберите опцию:")
    for key, value in options.items():
        print(f"{key}. {value}")
    choice = input("Введите номер опции: ")

    parity = determine_parity()
    if choice == '1':
        # Сегодня
        day = datetime.now().isoweekday()
        days = [day]
        parity = determine_parity()
    elif choice == '2':
        # Завтра
        day = (datetime.now() + timedelta(days=1)).isoweekday()
        if day == 7:
            print("Завтра воскресенье, пар нет.")
            return
        days = [day]
        parity = determine_parity()
    elif choice == '3':
        # На эту неделю
        days = list(range(1, 7))
        parity = determine_parity()
    elif choice == '4':
        # На следующую неделю
        days = list(range(1, 7))
        parity = determine_parity(week_offset=1)
    else:
        print("Неверный выбор.")
        return

    surname = input("Введите фамилию или фамилию и инициалы преподавателя: ").strip()

    teachers = search_teachers_in_files(files, surname)

    if len(teachers) == 0:
        print("Преподаватель не найден.")
        return

    if len(teachers) > 1:
        print("Найдено несколько преподавателей с такой фамилией:")
        for idx, teacher in enumerate(teachers, start=1):
            print(f"{idx}. {teacher}")
        choice = int(input("Выберите номер преподавателя: "))
        teacher = teachers[choice - 1]
    else:
        teacher = teachers[0]

    for day in days:
        schedule = find_teacher_schedule_in_files(files, day, parity, teacher)
        print(schedule)  # Debugging line to print the schedule
        print_schedule_for_day(schedule, teacher, day)

if __name__ == "__main__":
    main()