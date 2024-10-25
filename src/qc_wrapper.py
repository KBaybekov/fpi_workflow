#!/usr/bin/env python3

import sys
import pandas as pd
import os
import warnings
from utils import get_samples_in_dir_tree

warnings.filterwarnings("ignore")

def parse_args(args:list):
    if len(args) != 3:
        print("Использование: qc_wrapper.py qc_directory qc_data.xlsx")
        sys.exit(1)
    return args[1], args[2]

def read_qc_data(qc_data_file:pd.DataFrame) -> pd.DataFrame:
    if os.path.exists(qc_data_file):
        return pd.read_excel(qc_data_file)
    else:
        return pd.DataFrame(columns=['id',  'main_species_G1','95%_isolate_G1', '90%_isolate_G1', 'list_G1',
                                     'main_species_S','95%_isolate_S', '90%_isolate_S', 'list_S',
                                     'main_species_S1','95%_isolate_S1', '90%_isolate_S1', 'list_S1',
                                     '16S_list', 'contamination, %', 'total_reads'])
    
def get_sample_ids(kreports:list) -> list:
    sample_ids = []
    for s in kreports:
        basename = os.path.basename(s)
        sample = f'{basename.split("_")[0]}_{basename.split("_")[1]}'
        sample_ids.append(sample)
    return list(set(sample_ids))

def process_kreports(data_df:pd.DataFrame, sample_ids:list, kreports:list) -> pd.DataFrame:
    # Счётчик отсмотренных образцов
    i = 0

    for id in sample_ids:
        # проверяем наличия образца в исходной таблице
        if data_df['id'].isin([id]).any():
            i = finish_iteration(i)
            continue
        else:
            # Создаём пустой словарь для данных образца
            data = {'total_reads':0}
            new_row = {'id': id}
            
            
            # Отбираем репорты, относящиеся к образцу
            subset_kreports = [k for k in kreports if id in k]
            
            # Итерация по репортам; сначала обрабатываем репорты по контаминации
            for db_type in ['human', 'fungi', 'myco','16S']:
                # Находим индекс элемента, содержащего подстроку с указанной БД
                index = next((i for i, element in enumerate(subset_kreports) if db_type in element), None)
                # Если элемент найден, удаляем его
                if index is not None:
                    kr = subset_kreports.pop(index)
                else:
                    data[db_type] = {}
                # Извлекаем данные в виде словаря, обновляя его новыми значениями
                data = parse_kreport(file=kr, db_type=db_type, data=data)

            new_row['total_reads'] = data['total_reads']
            # Определяем процент контаминации и коэффициент поправки на неё (чем больше контаминация, тем меньше % составляет выявленный вид от общей массы)
            if isinstance(data['human'], int) and isinstance(data['fungi'], int):
                data['contamination'] = round((((data['human'] + data['fungi'])/(data['total_reads']))), 6)
                decontaminated_ratio = 1 - data['contamination']
            else:
                data['contamination'] = 'REANALYSIS'
                decontaminated_ratio = 1/100
            new_row['contamination, %'] = data['contamination']*100
            
            for db in ['myco','16S']:
                if db == '16S':
                    if data[db]:
                        sorted_ratios_16s = sort_species_by_abundance(taxa_data=data[db]['S']['taxas'],
                                                                               total_rank_fragments=data[db]['S']['total'],
                                                                               decontaminated_ratio=decontaminated_ratio)
                        new_row['16S_list'] = get_list_str(total=data['total_reads'], total_rank=data[db]['S']['total'], data=sorted_ratios_16s)
                    else:
                        new_row['16S_list'] = 'REANALYSIS'

                else:
                    if data[db]:
                        for rank in ['G1', 'S', 'S1']:
                            if data[db][rank]:
                                sorted_ratios_myco = sort_species_by_abundance(taxa_data=data[db][rank]['taxas'],
                                                                               total_rank_fragments=data[db][rank]['total'],
                                                                               decontaminated_ratio=decontaminated_ratio)

                                # Выбираем вид с наибольшим количеством ридов (он будет стоять первым)
                                main_species = next(iter(sorted_ratios_myco))
                                                                            
                                # Проверяем на условия 95% и 90%
                                is_95_isolate = sorted_ratios_myco[main_species] > 0.95
                                is_90_isolate = sorted_ratios_myco[main_species] >= 0.90

                                # Добавляем данные в строку
                                new_row[f'main_species_{rank}'] = main_species
                                new_row[f'95%_isolate_{rank}'] = is_95_isolate
                                new_row[f'90%_isolate_{rank}'] = is_90_isolate
                                new_row[f'list_{rank}'] = get_list_str(total=data['total_reads'], total_rank=data[db][rank]['total'], data=sorted_ratios_myco)
                            else:
                                # Если словарь ранга пустой, возвращаем пустую строку
                                new_row[f'main_species_{rank}'] = ''
                                new_row[f'95%_isolate_{rank}'] = False
                                new_row[f'90%_isolate_{rank}'] = False
                    
                    else:
                        # Если словарь репорта пустой, возвращаем пустую строку
                        new_row.update({'main_species_G1':'REANALYSIS','95%_isolate_G1':False, '90%_isolate_G1':False, 'list_G1':'REANALYSIS',
                                     'main_species_S':'REANALYSIS','95%_isolate_S':False, '90%_isolate_S':False, 'list_S':'REANALYSIS',
                                     'main_species_S1':'REANALYSIS','95%_isolate_S1':False, '90%_isolate_S1':False, 'list_S1':'REANALYSIS',})
                    
            # Добавляем новую строку в DataFrame
            data_df = data_df._append(new_row, ignore_index=True)
        i = finish_iteration(i)
        
    return data_df.copy()

def parse_kreport(file:str, db_type:str, data:dict) -> dict:
    """
    Обрабатывает данные репорта kraken2. Функция оставляет данные только указанного уровня (level) \
    и возвращает числовые значения в зависимости от типа анализа. Описание колонок:\n
    https://github.com/DerrickWood/kraken2/wiki/Manual#sample-report-output-format
    
    :param file: Репорт kraken2
    :param analysis_type: тип анализа:\n - если это качественный (qualitative), то нас интересует количество фрагментов,\
          отнесённых к тому или иному таксону;\n - если количественный (quantitative), то процентное соотношение количества \
            фрагментов для каждого таксона
    :param db_type: Тип БД. Все БД, кроме 16S, считаются БД для оценки контаминации
    :param data: Словарь с данными по конкретному образцу
    """
    '''col_of_interest = {'qualitative':'clade_frament',
                       'quantitative':'percentage'}'''
    # Чтение файла с данными и его форматирование
    df = read_kreport(file=file)
    # Обновляем данные о количестве ридов в образце
    if data['total_reads'] == 0:
        data['total_reads'] = df['taxon_fragment'].sum()

    # Получаем данные по видам для 16S
    if db_type == '16S':
        data[db_type] = get_db_data(df=df, ranks=['S'])
    
    # Получаем данные по видам внутри Mycobacteriaceae
    elif db_type == 'myco':
        data[db_type] = get_db_data(df=df, ranks=['G1', 'S', 'S1'])
    else:
        data[db_type] = get_db_data(df=df, contaminants=True)
    return data

def read_kreport(file:str) -> pd.DataFrame:
    df = pd.read_csv(file, sep='\t', header=None)
    # Присвоение имен столбцам
    df.columns = ['percentage', 'clade_frament', 'taxon_fragment', 'taxon_minimizers',
                  'est_taxon_minimizers', 'rank', 'NCBI_tax_id', 'taxonomy']
    # Убираем пробелы в первой колонке, если значение не равно 100.00
    df['percentage'] = df['percentage'].apply(lambda x: x.strip() if isinstance(x, str) else x)
    # Убираем пробелы в последней колонке (перед научными названиями)
    df['taxonomy'] = df['taxonomy'].str.strip()
    return df

def get_db_data(df:pd.DataFrame, ranks:list=[], contaminants:bool=False) -> dict:
    db_data = {}
    if contaminants:
        try:
            # Извлекаем идентифицированное количество фрагментов
            db_data = int(df[df['rank'] == 'R']['clade_frament'].values[0])
        except IndexError:
            db_data = 'REANALYSIS'

    else:
        # Итерируем сбор данных по разным кладам
        if len(df) != 0:
            for rank in ranks:
                db_data[rank] = {}
                # Определяем, по какому таксономическому рангу будем проводить подсчёт
                subset_df = df[df['rank'] == rank].reset_index(drop=True)
                if len(subset_df) != 0:
                    # Подсчитываем общее количество идентифицированных до этого уровня ридов
                    db_data[rank].update({'total': subset_df['taxon_fragment'].sum()})
                    db_data[rank]['taxas'] = {}
                    for row in range(len(subset_df)):
                        indicator = subset_df.loc[row, 'taxon_fragment']
                        # Сохраняем данные о количестве ридов в данной кладе, если их больше 0
                        if indicator != 0:
                            taxa = subset_df.loc[row, 'taxonomy']
                            db_data[rank]['taxas'].update({taxa:indicator})
        

    
    return db_data

def sort_species_by_abundance(taxa_data:dict, total_rank_fragments:int, decontaminated_ratio:float) -> dict:
    # Получаем список представленных таксонов и процент, который они составляют от общего числа классифицированных ридов
    ratio = {k: v*decontaminated_ratio/total_rank_fragments for k, v in taxa_data.items()}
    # Сортируем их по убыванию
    sorted_ratio = {k: v for k, v in sorted(ratio.items(), key=lambda item: item[1], reverse=True)}
    return sorted_ratio

def get_list_str(total:int, total_rank:int, data:dict) -> str:
    s1 = f'Идентифицировано: {round((total_rank/total*100), 2)}% ридов ({total_rank}).'
    s2 = '\n\n'
    s3 = '\n'.join([f"{species}: {round(value*100, 2)}%" for species, value in data.items() if round(value*100, 2) !=0])
    return f"{s1}{s2}{s3}"

def finish_iteration(i:int):
    print(f'\r{i+1}', end='')
    return i + 1

def main():
    """
    Основная функция. Читает файл с данными, сравнивает со списком файлов в указанной директории и добавляет новые записи
    """
       
    qc_dir, qc_data_file = parse_args(sys.argv)
    # Чтение qc файла
    data_df = read_qc_data(qc_data_file)
    kreports = get_samples_in_dir_tree(dir=qc_dir, extensions=('.kreport'))
    sample_ids = get_sample_ids(kreports)
    print(f'Найдено {len(sample_ids)}')
    data_df = process_kreports(data_df, sample_ids, kreports)
    data_df.to_excel(qc_data_file, index=False)


if __name__ == "__main__":
    main()