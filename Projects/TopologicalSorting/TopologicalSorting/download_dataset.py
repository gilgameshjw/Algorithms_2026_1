import urllib.request

url = "https://snap.stanford.edu/data/cit-HepTh.txt.gz"
filename = "cit-HepTh.txt.gz"

print("Downloading dataset...")

urllib.request.urlretrieve(url, filename)

print("Download finished!")
print("Saved as:", filename)