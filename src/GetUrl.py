from urllib.request import urlopen
import re
import json
import os.path
from pathlib import Path
from shutil import unpack_archive
import requests
import psycopg2
from _datetime import datetime


try:
    conn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='password'")
except:
   print ("I am unable to connect to the database")

#database queries
#consider removing time
# sql_insertToCve = "INSERT into cve(id, publisheddate, lastmodifieddate, description) VALUES(%s, %s, %s, %s);"
# 
# def addToCveTbl(cve_id, publishedDate, lastModDate, description):
#     #cur = conn.cursor()
#     cur.execute(sql_insertToCve, (cve_id, publishedDate, lastModDate, description))
#     
#     conn.commit()
    #cur.close()
    
sql_insertToBaseMetricV2 = "INSERT into basemetricv2 (cve_id, access_vector, base_score, exploitability_score, impact_score, severity, vector_string) VALUES (%s, %s, %s, %s,%s, %s, %s)"
def addToBaseMetricV2(cve_id, baseMetricV2):
    if(baseMetricV2 is not None):
        print("baseMetric V2")
        cvssV2 = baseMetricV2.get("cvssV2")
        accessVector = cvssV2.get("accessVector")
        baseScore = cvssV2.get("baseScore")
        exploitabilityScore = baseMetricV2.get("exploitabilityScore")
        impactScore = baseMetricV2.get("impactScore")
        severity = baseMetricV2.get("severity")
        vectorString = cvssV2.get("vectorString")
        print(cvssV2)
        print(accessVector)
        print(baseScore)
        print(exploitabilityScore)
        print(impactScore)
        print(severity)
        print(vectorString)    
     #cve_id, accessVector, baseScore, exploitabilityScore, impactScore, severity, vectorString
#     cur.execute(sql_insertToBaseMetricV2, (cve_id, accessVector, baseScore, exploitabilityScore, impactScore, severity, vectorString))  

sql_insertToBaseMetricV3 = "INSERT into basemetricv3 (cve_id, attack_vector, base_score, base_severity, exploitability_score, impact_score, vector_string) VALUES (%s, %s, %s, %s,%s, %s, %s)"
def addToBaseMetricV3(cve_id, baseMetricV3):
    if(baseMetricV3 is not None):
        print("baseMetric V3")
        cvssV3 = baseMetricV3.get("cvssV3")
        attackVector = cvssV3.get("attack_vector")
        baseScore = cvssV3.get("baseScore")
        exploitabilityScore = baseMetricV3.get("exploitabilityScore")
        impactScore = baseMetricV3.get("impactScore")
        baseSeverity = cvssV3.get("baseSeverity")
        vectorString = cvssV3.get("vectorString")  
        print(cvssV3) 
        print(attackVector)
        print(exploitabilityScore)
        print(impactScore)
        print(baseSeverity)
        print(vectorString)


sql_selectVendor = "SELECT id FROM vendorinfo where vendor_name=%s and product_name=%s"        
def getVendorID(vendorName, productName):
    cur = conn.cursor()
    cur.execute(sql_selectVendor, (vendorName, productName))
    result = cur.fetchone()
    if(result is None):
        return -1
    else:
        return result[0]

#todo add retry       
# website = urlopen("https://nvd.nist.gov/vuln/data-feeds#JSON_FEED")
# html = website.read().decode('utf-8')
# 
# links = re.findall('https://.*json.zip', html)
# print(links)   

####################
##Code to download file

# current_dir = Path.cwd()
# #make temp dir
# cveDir = Path("cve_data_files")
# if not cveDir.exists():
#     cveDir.mkdir(mode=0o777, parents=True, exist_ok=False)
# 
# data_url = 'https://nvd.nist.gov/feeds/json/cve/1.0/nvdcve-1.0-modified.json.zip'
# zipFile = cveDir.joinpath(Path(data_url).name)
# 
# print('Downloading', data_url)
# resp = requests.get(data_url)
# print("Saving to", zipFile)
# zipFile.write_bytes(resp.content)
# 
# unpack_archive(str(zipFile), extract_dir=str(cveDir))
####################

#cur = conn.cursor()
cveDir = Path("cve_data_files") #added here for testing
for fpath in cveDir.glob('*.json'):
    with open(fpath, "r") as read_file:
        data = json.load(read_file)
        for cve_item in data["CVE_Items"]:
            cve = cve_item.get("cve")
            cve_meta = cve.get("CVE_data_meta")
            cve_id = cve_meta.get("ID")
            
            publishedDate = cve_item.get("publishedDate")
           # d = datetime.strptime(publishedDate, "%Y-%mm-%d").date()
            lastModifiedDate = cve_item.get("lastModifiedDate")
            
            
            cveDescription = cve.get("description")
            descriptionData = cveDescription.get("description_data")
            descriptionDataVal = descriptionData[0].get("value")
            
           # addToCveTbl(cve_id, publishedDate, lastModifiedDate, descriptionDataVal)
            
            affects = cve.get("affects")
            vendor = affects.get("vendor")
            for vendor_item in vendor.get("vendor_data"):
                vendor_name = vendor_item.get("vendor_name")
                products = vendor_item.get("product")
                for product_item in products["product_data"]:
                    product_name = product_item.get("product_name")
                    version_data = product_item.get("version_data")
                
            #print(getVendorID('test', 'test'))
            
            impact = cve_item.get("impact")
            baseMetricV2 = impact.get("baseMetricV2")
            addToBaseMetricV2(cve_id, baseMetricV2)
            
            baseMetricV3 = impact.get("baseMetricV3")
            addToBaseMetricV3(cve_id, baseMetricV3)
            
            print(descriptionDataVal)
            print(cve_id)
            print(publishedDate)
            
#cur = conn.cursor()

   
#cur = conn.cursor()
# cur.execute("SELECT * from vendorinfo")
# for record in cur:
#      print(record)
#cur.close()
       
#print(data)
        
#?Need to check if given json file matches given schema file?
#ex: https://medium.com/grammofy/handling-complex-json-schemas-in-python-9eacc04a60cf
#Need to close database http://www.postgresqltutorial.com/postgresql-python/insert/

        

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

