from urllib.request import urlopen
import re
import json
import os.path
from pathlib import Path
from shutil import unpack_archive
import requests
import psycopg2
from _datetime import datetime
import sys

conn = None
dbConnectInfo = "dbname='postgres' user='postgres' host='localhost' password='password'"
jsonFeedUrl = "https://nvd.nist.gov/vuln/data-feeds#JSON_FEED"

#database queries
#consider removing time
sql_insertToCve = "INSERT into cve(id, publisheddate, lastmodifieddate, description) VALUES(%s, %s, %s, %s)" 
def addToCveTbl(cve_id, publishedDate, lastModDate, description, conn):
    cur = conn.cursor()
    cur.execute(sql_insertToCve, (cve_id, publishedDate, lastModDate, description))     
    conn.commit()
    cur.close()
    
sql_insertToBaseMetricV2 = "INSERT into basemetricv2 (cve_id, access_vector, base_score, exploitability_score, impact_score, severity_value, vector_string) VALUES (%s, %s, %s, %s,%s, %s, %s)"
def addToBaseMetricV2(cve_id, baseMetricV2, conn):
    if(baseMetricV2 is not None):
        cur = conn.cursor()
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
     
        cur.execute(sql_insertToBaseMetricV2, (cve_id, accessVector, baseScore, exploitabilityScore, impactScore, severity, vectorString))
        conn.commit()
        cur.close()  

sql_insertToBaseMetricV3 = "INSERT into basemetricv3 (cve_id, attack_vector, base_score, base_severity, exploitability_score, impact_score, vector_string) VALUES (%s, %s, %s, %s,%s, %s, %s)"
def addToBaseMetricV3(cve_id, baseMetricV3, conn):
    if(baseMetricV3 is not None):
        cur = conn.cursor()
        print("baseMetric V3")
        cvssV3 = baseMetricV3.get("cvssV3")
        attackVector = cvssV3.get("attackVector")
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
        cur.execute(sql_insertToBaseMetricV3, (cve_id, attackVector, baseScore, baseSeverity, exploitabilityScore, impactScore, vectorString))
        conn.commit()
        cur.close()


sql_selectVendor = "SELECT id FROM vendorinfo where vendor_name=%s and product_name=%s"        
def getVendorID(vendorName, productName, conn):
    cur = conn.cursor()
    cur.execute(sql_selectVendor, (vendorName, productName))
    result = cur.fetchone()
    if(result is None):
        return -1
    else:
        return result[0]
    
sql_insertVendor = "INSERT INTO vendorinfo (vendor_name, product_name) values (%s, %s) RETURNING id"
def addVendorToDB(vendorName, productName, conn):
    cur = conn.cursor()
    cur.execute(sql_insertVendor, (vendorName, productName))
    conn.commit()
    vendorId = cur.fetchone()[0]
    cur.close()
    return vendorId

sql_insertAffectedVendors = "INSERT INTO affectedvendors (id, vendor_id, version) values (%s, %s, %s)"
def addToAffectedVendors(cve_id, affects, conn):    
    vendor = affects.get("vendor")
    for vendor_item in vendor["vendor_data"]:
        vendor_name = vendor_item.get("vendor_name")
        products = vendor_item.get("product")
        for product_item in products["product_data"]:
            product_name = product_item.get("product_name")
            vendorId = getVendorID(vendor_name, product_name, conn)
            if(vendorId == -1):
                 #insert into vendorInfo table
                vendorId = addVendorToDB(vendor_name, product_name, conn)
            print(vendorId)
            versions = product_item.get("version")
            for version_item in versions["version_data"]:
                version_value = version_item.get("version_value")
                
                print(version_value)
                print(cve_id)
                cur = conn.cursor()
                cur.execute(sql_insertAffectedVendors, (cve_id, vendorId, version_value))
                conn.commit()
                cur.close()

sql_insertCPE = "INSERT INTO cpe (cve_id, cpe22uri, cpe23uri, version_start_excluding, version_start_including, version_end_excluding, version_end_including) values (%s, %s, %s, %s, %s, %s, %s)"                
def addToCpe(cve_id, configurations, conn):
    cur = conn.cursor()
    for node_item in configurations["nodes"]:                
        for cpe_item in node_item["cpe"]:
            isVulnerable = cpe_item.get("vulnerable")
            if isVulnerable:
                cpe22Uri = cpe_item.get("cpe22Uri")
                cpe23Uri = cpe_item.get("cpe23Uri")
                versionStartExcluding = cpe_item.get("versionStartExcluding")
                versionStartIncluding = cpe_item.get("versionStartIncluding")
                versionEndExcluding = cpe_item.get("versionEndExcluding")
                versionEndIncluding = cpe_item.get("versionEndIncluding")
                try:#todo have a generic execute query method to reduce 'try' and 'except' text
                    cur.execute(sql_insertCPE, (cve_id, cpe22Uri, cpe23Uri, versionStartExcluding, versionStartIncluding, versionEndExcluding, versionEndIncluding))
                    conn.commit()
                except Exception as exc:
                    print("Error executing SQL: %s"%exc)
    cur.close()
 
def getDBConnection(dbConnectInfo):
    try:
        conn = psycopg2.connect(dbConnectInfo)
        return conn
    except:
        sys.exit("I am unable to connect to the database") 
                                        
#todo add retry
def getLinks():       
    website = urlopen(jsonFeedUrl)
    html = website.read().decode('utf-8')
      
    links = re.findall('https://.*json.zip', html)
    print(links)
    return links   

def main():
    links = getLinks()
    cveDir = Path("cve_data_files")
    if not cveDir.exists():
        cveDir.mkdir(mode=0o777, parents=True, exist_ok=False)
    
    for link_item in links:
        zipFile = cveDir.joinpath(Path(link_item).name)
        print('Downloading', link_item)
        resp = requests.get(link_item)
        print("Saving to", zipFile)
        zipFile.write_bytes(resp.content)
        unpack_archive(str(zipFile), extract_dir=str(cveDir))
        for fpath in cveDir.glob('*.json'):           
            print(fpath)
            #get a new connection for each file so we don't keep a connection open for too long
            dbConn = getDBConnection(dbConnectInfo)    
            processData(fpath, dbConn)
            if dbConn is not None:
                dbConn.close()
    
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
# cveDir = Path("cve_data_files") #added here for testing
# for fpath in cveDir.glob('*.json'):
#     with open(fpath, "r") as read_file:
#         data = json.load(read_file)
def processData(fpath, conn):
    with open(fpath, "r") as read_file:
        data = json.load(read_file)
        for cve_item in data["CVE_Items"]:
            cve = cve_item.get("cve")
            cve_meta = cve.get("CVE_data_meta")
            cve_id = cve_meta.get("ID")
            
            publishedDate = cve_item.get("publishedDate")
            lastModifiedDate = cve_item.get("lastModifiedDate")
            cveDescription = cve.get("description")
            descriptionData = cveDescription.get("description_data")
            descriptionDataVal = descriptionData[0].get("value")
            
            addToCveTbl(cve_id, publishedDate, lastModifiedDate, descriptionDataVal, conn)
            
            affects = cve.get("affects")
            addToAffectedVendors(cve_id, affects, conn)
            
            configurations = cve_item.get("configurations")
            addToCpe(cve_id, configurations, conn)
            
            impact = cve_item.get("impact")
            baseMetricV2 = impact.get("baseMetricV2")
            addToBaseMetricV2(cve_id, baseMetricV2, conn)
            
            baseMetricV3 = impact.get("baseMetricV3")
            addToBaseMetricV3(cve_id, baseMetricV3, conn)
                        
            print(cve_id)
            
def startProcess(url, dbConnInfo):
    if url is not None:
        jsonFeedUrl = url
    
    if dbConnInfo is not None:
        dbConnectInfo = dbConnInfo
        
    main()
            
#cur = conn.cursor()

#comment out so it will not execute when import
#main()
  
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

