import sys
from utils import read_qc_file
import pandas as pd
import warnings

warnings.filterwarnings("ignore")


def parse_args(args:list):
    if len(args) != 5:
        print("Использование: quast_parser.py sample_id species busco.json busco_qc_data.xlsx")
        sys.exit(1)
    return args[1], args[2], args[3], args[4]

def get_quast_data(quast_report:str, species:str, id:str, cols:list) -> dict:
    quast_data = pd.read_csv(quast_report, sep='\t')
    new_row = {'id':id, 'Species':species}
    for col in cols:
        if cols.index(col) < 2:
            continue
        else:
            if col in quast_data.columns.values:
                pair = {col:quast_data.at[0,col]}
            else:
                pair = {col:''}
            new_row.update(pair)
    return new_row

def main():
    """
    Основная функция. Читает файл с данными, добавляет новые записи
    """
    df:pd.DataFrame

    id, species, quast_report, qc_data_file = parse_args(sys.argv)
    quast_cols = ['SRR', 'Species', 'Reference mapped (%)', 'Reference properly paired (%)', '# contigs',  'Largest contig', 'Reference length', \
              'Total aligned length', 'Unaligned length', 'Total length', 'Duplication ratio', 'GC (%)', 'Reference GC (%)', \
              'Genome fraction (%)', 'N50', 'NG50', 'N90', 'NG90', 'auN', 'auNG', 'L50', 'LG50', 'L90', 'LG90', 'NA50', \
              'NGA50', 'NA90', 'NGA90', 'auNA', 'auNGA', 'LA50', 'LGA50', 'LA90', 'LGA90', \
              '# misassemblies', '# misassembled contigs', 'Misassembled contigs length', '# structural variations', \
              "# N's per 100 kbp", '# mismatches per 100 kbp', \
              '# indels per 100 kbp', 'Largest alignment']
    # Чтение qc файла
    df = read_qc_file(filepath=qc_data_file, cols=quast_cols)
    data = get_quast_data(id=id, quast_report=quast_report, cols=quast_cols, species=species)
    # Добавляем новую строку в DataFrame
    df = df._append(data, ignore_index=True)
    df.to_excel(qc_data_file, index=False)


if __name__ == "__main__":
    main()