from utils import load_yaml
import os

proj_path = os.path.dirname(os.path.realpath(__file__).replace('src', 'config'))
refs = load_yaml(file_path=os.path.join(proj_path, 'species_ref_genomes.yaml'))

print(refs)

def main():
    """
    Основная функция. Читает файл со списком видов и айди их референсов, сравнивает со списком файлов в директории сгеномами, \
         если не находит геномы - сообщает об этом. Затем проверяет в указанной директории наличие генома и его индексов, \
            при их отсутствии - копирует и индексирует.
    """
       
    qc_dir, qc_filepath = parse_args(sys.argv)
    kreken2_columns=['id',  'main_species_G1', 'main_G1_%', '95%_isolate_G1', '90%_isolate_G1', 'list_G1',
                                     'main_species_S', 'main_S_%', '95%_isolate_S', '90%_isolate_S', 'list_S',
                                     'main_species_S1', 'main_S1_%', '95%_isolate_S1', '90%_isolate_S1', 'list_S1',
                                     '16S_list', 'contamination, %', 'total_reads']
    # Чтение qc файла
    data_df = read_qc_file(qc_filepath, cols=kreken2_columns)
    kreports = get_samples_in_dir_tree(dir=qc_dir, extensions=('.kreport'))
    sample_ids = get_sample_ids(kreports)
    print(f'Найдено {len(sample_ids)}')
    data_df = process_kreports(data_df, sample_ids, kreports)
    data_df.to_excel(qc_filepath, index=False)


if __name__ == "__main__":
    main()