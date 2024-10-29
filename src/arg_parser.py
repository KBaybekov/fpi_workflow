import argparse
import os
from src.utils import load_yaml

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
    parser.add_argument('-db', '--debug', default=False, help=arg_descriptions['debug'])
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

    # Если мы выравниваем NTM на реф геном, то нам нужно заменить в аргументах default ref на ref нужного вида.
    # Для этого снабжаем пайплайн словарём с указанием id и превалирующего в нём вида
    if any(['variant_calling' in module for module in args.modules]):
        ntm_list = load_yaml(file_path=f'{configs}/ntm_list.yaml')
        ref_list = load_yaml(file_path=f'{configs}/species_ref_genomes.yaml')
        refs4ids = {key: ref_list[val] for key,val in ntm_list}
        setattr(args, 'refs4ids', refs4ids)

    
    # Преобразуем Namespace в словарь
    args = vars(args)  # Преобразуем объект Namespace в словарь

    return args