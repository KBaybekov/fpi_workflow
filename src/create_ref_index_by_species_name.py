from utils import load_yaml,copy_files,get_samples_in_dir
import os
import sys
import subprocess


def parse_args(args:list):
    if len(args) != 2:
        print("Использование: create_ref_index_by_species_name.py dir_to_check")
        sys.exit(1)
    return args[1]

def check_for_idxd_genomes(path:str) -> tuple:
    """Возвращает кортеж, состоящий из двух списков: список скопированных геномов и список геномов без какого-то из индексов (дочерен первому списку)
    
    :param path: Где ищем геномы"""
    found_genomes = get_samples_in_dir(dir=path, extensions=('.fna', '.fa'))
    idxd_genomes = set(get_samples_in_dir(dir=path, extensions=('.bwt')))
    unidxd_genomes = [gnm for gnm in found_genomes if not any(gnm in idxd for idxd in idxd_genomes)]
    return (found_genomes, unidxd_genomes)

def index_genomes(path:str, to_index:list) -> None:
    for genome in to_index:
        print(genome)
        filepath = os.path.join(path, genome)
        cmds = {'bwa':'bwa index {}',
                'meme': 'cd /home/data/Programms/BWA-MEME/ && bwa-meme index -a meme {} -t 48 && build_rmis_dna.sh {}'
                }
        for title,cmd in cmds.items():
            #print(cmd.format(filepath))
            result = subprocess.run(cmd.format(filepath), shell=True, capture_output=True, text=True, executable="/bin/bash").returncode
            print(f'\t{title}: {result}')


def main():
    """
    Основная функция. Читает файл со списком видов и айди их референсов, сравнивает со списком файлов в директории сгеномами, \
    если не находит геномы - сообщает об этом. Затем проверяет в указанной директории наличие генома и его индексов, \
    при их отсутствии - копирует и индексирует.
    """
    unindexed_genomes:list

    # Папка, откуда тащатся геномы в случае их отсутствия 
    ncbi_dir = '/home/data/REFERENCE_FILES/NCBI_datasets/Mycobacteriaceae/fna/'

    # Собираем данные о геномах, расположенных в указанной папке
    folder = parse_args(sys.argv)
    copied_genomes, unindexed_genomes = check_for_idxd_genomes(folder)
    
    # Формируем словарь с содержанием организм:id референсной геномной сборки 
    proj_path = os.path.dirname(os.path.realpath(__file__).replace('src', 'config'))
    ref_dict = load_yaml(file_path=os.path.join(proj_path, 'species_ref_genomes.yaml'))
    transposed_ref_dict = {key:val for val,key in ref_dict.items()}

    # Ищем, чьи геномы нужно перенести из папки со всеми геномами
    genomes_to_copy = [id for id in ref_dict.values() if not any(id in file for file in copied_genomes)]

    # Добавляем в список к геномам для индексирования
    unindexed_genomes.extend(genomes_to_copy)

    #Копируем, а затем индексируем найденные геномы
    unfound_genomes = copy_files(src_path=ncbi_dir, dest_path=folder,
                                 to_copy=genomes_to_copy,
                                 prefix_mask='*', second_part='arg_list', suffix_mask='*.fna')
    if unfound_genomes:
        print("Не найдены геномы следующих организмов:")
        for id in unfound_genomes:
            print(transposed_ref_dict[id])

    # Индексируем неидексированное   
    index_genomes(path=folder, to_index=unindexed_genomes)

    # Повторно проверяем индексы
    _c, unindexed_genomes = check_for_idxd_genomes(folder)

    if unindexed_genomes:
        print("Не проиндексированы:")
        for id in unindexed_genomes:
            print(f"{transposed_ref_dict[id]} ({id})")
    else:
        print("Success, we're done here!")

if __name__ == "__main__":
    main()