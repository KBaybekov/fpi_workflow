import argparse
import os
import yaml

def parse_cli_args():
    """
    Функция для обработки аргументов командной строки
    """
    configs = os.path.dirname(os.path.realpath(__file__).replace('src', 'config'))
    arg_descriptions = load_yaml(f'{configs}/arg_descriptions.yaml', critical=True)
        
    parser = argparse.ArgumentParser(
        description=arg_descriptions['prolog'], 
        epilog=arg_descriptions['epilog']
    )
    
    # Основные аргументы с описаниями из YAML
    parser.add_argument('-i', '--input_dir', required=True, help=arg_descriptions['input_dir'])
    parser.add_argument('-o', '--output_dir', required=True, help=arg_descriptions['output_dir'])
    parser.add_argument('-t', '--threads', default='', help=arg_descriptions['threads'])
    parser.add_argument('-r', '--ref_fasta', default='', help=arg_descriptions['ref_fasta'])
    parser.add_argument('-mc', '--machine', required=True, help=arg_descriptions['machine'])
    parser.add_argument('-m', '--modules', default='', help=arg_descriptions['modules'])
    parser.add_argument('-es', '--exclude_samples', default='', help=arg_descriptions['exclude_samples'])
    parser.add_argument('-is', '--include_samples', default='', help=arg_descriptions['include_samples'])
    parser.add_argument('-dm', '--demo', default='', help=arg_descriptions['demo'])
    parser.add_argument('-pp', '--project_path', default='', type=str, help=arg_descriptions['project_path'])
    parser.add_argument('-s', '--subfolders', default=False, help=arg_descriptions['subfolders'])

    # Парсим аргументы
    args = parser.parse_args()

    # Обработка списков образцов
    list_args = ['exclude_samples', 'include_samples']
    for arg in list_args:
        value = getattr(args, arg)  # Динамически получаем значение аргумента
        setattr(args, arg, value.split(',') if value else [])

    if args.modules != '':
        args.modules = args.modules.split(',')

    # Загрузка значений по умолчанию
    default_values = load_yaml(f"{configs}/default_values.yaml",
                               critical=True)

    # Присваивание значений по умолчанию в случае отсутствия аргумента в CMD
    for arg, default_value in default_values.items():
        if getattr(args, arg) == '':
            setattr(args, arg, default_value)
    
    # Преобразуем Namespace в словарь
    args = vars(args)  # Преобразуем объект Namespace в словарь

    return args

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
