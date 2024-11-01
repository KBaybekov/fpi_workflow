import os

regions_file = '/media/sf_DATA/tmp/blast/16S_hits_w15_perc100_ungapped.tsv'

with open(regions_file, 'r') as r:
    data = r.read().split('\n')

coords_list = []
for unit in data:
    if unit.count('\t') == 2:
        coords = unit.split('\t')
        contig = coords[0]
        start = int(coords[1]) - 200 if int(coords[1]) >= 200 else 0
        end = int(coords[2]) + 200
        coords_list.append(f'{contig}:{start}-{end}')
print(f'samtools faidx {" ".join(coords_list)}')
