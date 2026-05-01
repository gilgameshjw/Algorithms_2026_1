import gzip
import shutil

with gzip.open('cit-HepTh.txt.gz', 'rb') as f_in:
    with open('dataset.txt', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

print("Dataset extracted to dataset.txt")