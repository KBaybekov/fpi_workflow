import os
import pandas as pd
import yaml

def load_yaml(file_path:str, critical:bool = False, subsection:str = ''):
    """
    Универсальная функция для загрузки данных из YAML-файла.

    :param file_path: Путь к YAML-файлу. Ожидается строка, указывающая на местоположение файла с данными.
    :param critical: Возвращает ошибку, если файл не найден
    :param subsection: Опциональный параметр. Если передан, функция вернёт только данные из указанной
                       секции (например, конкретного этапа пайплайна). Если пусто, возвращаются все данные.
                       По умолчанию - пустая строка, что означает возврат всего содержимого файла.
    
    :return: Возвращает словарь с данными из YAML-файла. Если указан параметр subsection и он присутствует
             в YAML, возвращается соответствующая секция, иначе — всё содержимое файла.
    """
    # Открываем YAML-файл для чтения
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)  # Загружаем содержимое файла в словарь с помощью safe_load
        
        # Если subsection не указан, возвращаем весь YAML-файл
        if subsection == '':
            return data
        else:
            # Если subsection указан и существует в файле, возвращаем только эту секцию
            if subsection  in data.keys():
                return data[subsection]
            else:
                raise ValueError(f"Раздел '{subsection}' не найден в {file_path}")
    except FileNotFoundError as e:
        # Если файл не найден, возвращаем пустой словарь или ошибку, если данные необходимы для дальнейшей работы
        if critical:
            raise FileNotFoundError(f"Не найден: {file_path}")
        return {}
    
def save_yaml(filename, path, data):
    """
    Сохраняет словарь в файл в формате YAML.
    
    :param filename: Имя файла для сохранения (например, 'config.yaml')
    :param path: Путь к директории, где будет сохранён файл
    :param data: Словарь с данными, которые нужно сохранить в YAML
    """
    # Полный путь к файлу
    file_path = f'{path}{filename}.yaml'

    # Записываем данные в YAML-файл
    with open(file_path, 'w') as yaml_file:
        yaml.dump(data, yaml_file, default_flow_style=False, sort_keys=False)


def update_yaml(file_path: str, new_data: dict):
    """
    Обновляет YAML-файл, считывая и перезаписывая его новыми данными
    :param file_path: путь к файлу в виде строки
    :param new_data: данные в виде словаря
    """
    # Шаг 1: Загрузить текущие данные из YAML
    try:
        with open(file_path, 'r') as file:
            current_data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        current_data = {}  # Если файл не найден, создаём пустой словарь

    # Шаг 2: Обновить значения существующих ключей
    for key, value in new_data.items():
        if key in current_data:
            current_data[key].update(value)  # Обновляем только значения
        else:
            current_data[key] = value  # Добавляем новый ключ, если его нет

    # Шаг 3: Записать обновлённые данные обратно в YAML
    with open(file_path, 'w') as file:
        yaml.dump(current_data, file, default_flow_style=False)

def get_samples_in_dir_tree(dir:str, extensions:tuple) -> list:
    """
    Генерирует список файлов, проходя по дереву папок, корнем которого является dir.
    Выдаёт ошибку, если итоговый список пустой.

    :param dir: Директория, где искать файлы.
    :param extensions: Кортеж расширений файлов для поиска.
    :return: Список файлов с путями.
    """
    files = []
    for root, _ds, fs in os.walk(dir):
        samples = [os.path.join(root, f) for f in fs 
                    if f.endswith(extensions)]
        files.extend(samples)
    if not files:
        raise ValueError("Образцы не найдены. Проверьте входные и исключаемые образцы, а также директорию с исходными файлами.")
    return files

def read_qc_file(filepath:str, cols:list, file_type:str='xlsx', separator:str=',') -> pd.DataFrame:
    if file_type == 'xlsx':
        if os.path.exists(filepath):
            return pd.read_excel(filepath)
        else:
            return pd.DataFrame(columns=cols)
    elif file_type == 'csv':
        if os.path.exists(filepath):
            return pd.read_csv(filepath, sep=separator)
        else:
            return pd.DataFrame(columns=cols)
    else:
        raise ValueError('Неизвестный тип файла.')