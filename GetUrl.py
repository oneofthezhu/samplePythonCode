from urllib.request import urlopen
import re
import json
import os.path
from pathlib import Path
from shutil import unpack_archive
import requests


website = urlopen("https://nvd.nist.gov/vuln/data-feeds#JSON_FEED")
html = website.read().decode('utf-8')

links = re.findall('https://.*json.zip', html)
print(links)   


current_dir = Path.cwd()
#make temp dir
cveDir = Path("cve_data_files")
if not cveDir.exists():
    cveDir.mkdir(mode=0o777, parents=True, exist_ok=False)

data_url = 'https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-modified.json.zip'
zipFile = cveDir.joinpath(Path(data_url).name)

print('Downloading', data_url)
resp = requests.get(data_url)
print("Saving to", zipFile)
zipFile.write_bytes(resp.content)

unpack_archive(str(zipFile), extract_dir=str(cveDir))
for fpath in cveDir.glob('*.json'):
    with open(fpath, "r") as read_file:
        data = json.load(read_file)
       
        

        

# 
# print(data)    

'''
*Create the db and tables first before processing json files
*Get list of links
*Have a function that can process x number of links; default is all links on page
*Add log like "print('Downloading', DATA_URL)"
*Add tests
url = 'https://codeload.github.com/fogleman/Minecraft/zip/master'
#Need to clean up downloaded files when done (batch clean up)
 
# downloading with requests
 

# import the urllib library
import urllib
 
# Copy a network object to a local file
urllib.urlretrieve(url, "minemaster.zip")

'''

