import sys
import json
from utils import read_qc_file
import pandas as pd
import warnings

warnings.filterwarnings("ignore")


def parse_args(args:list):
    if len(args) != 4:
        print("Использование: busco_parser.py sample_id busco.json busco_qc_data.xlsx")
        sys.exit(1)
    return args[1], args[2], args[3]

def get_busco_data(id:str, busco_json:str, cols:list) -> dict:
    with open(busco_json) as json_data:
        d = json.load(json_data) 
    new_row = {'id':id}
    for col in cols:
        if col in d.keys():
            new_row.update({col:d['results'][col]})
    return new_row

def main():
    """
    Основная функция. Читает файл с данными, добавляет новые записи
    """
    df:pd.DataFrame

    id, busco_report, qc_data_file = parse_args(sys.argv)
    busco_cols = ['id',"Complete percentage","Complete BUSCOs",\
              "Single copy percentage","Single copy BUSCOs",\
              "Multi copy percentage","Multi copy BUSCOs",\
              "Fragmented percentage","Fragmented BUSCOs",\
              "Missing percentage","Missing BUSCOs"]
    # Чтение qc файла
    df = read_qc_file(filepath=qc_data_file, cols=busco_cols)
    if id not in df['id']:
        data = get_busco_data(id=id, busco_json=busco_report, cols=busco_cols)
        # Добавляем новую строку в DataFrame
        #df._append(data, ignore_index=True)
        df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
        print(df)
        df.to_excel(qc_data_file, index=False)


if __name__ == "__main__":
    main()