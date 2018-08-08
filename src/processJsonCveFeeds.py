from urllib.request import urlopen
import re
import json
from pathlib import Path
from shutil import unpack_archive
import requests
import psycopg2
import sys
import shutil
from datetime import datetime
import os

conn = None
dbConnectInfo = "dbname='postgres' user='postgres' host='localhost' password='password'"
jsonFeedUrl = "https://nvd.nist.gov/vuln/data-feeds#JSON_FEED"

#create tables based on schema   
def setupDB(dbConnInfo):
    if dbConnInfo is None:
        dbConnInfo = dbConnectInfo
        
    dbSetupConn = getDBConnection(dbConnInfo)
    sql_file = open('nvd_schema.sql', 'r')
    dbConnSetupCur = dbSetupConn.cursor()
    dbConnSetupCur.execute(sql_file.read())
    sql_file.close()
    dbSetupConn.commit()
    dbConnSetupCur.close()
    dbSetupConn.close()

    
#database queries
sql_selectCve = "SELECT lastmodifieddate FROM cve where id=%s"
def getCveLastModDateFromTbl(cve_id, conn):
    cur = conn.cursor()
    try:
        cur.execute(sql_selectCve, [cve_id])
        conn.commit()
        
        if cur.rowcount > 0:    
            result = cur.fetchone()
            return result[0]
        else:
            return -1
    except Exception as err:
        print("Error executing SQL: %s"%err)
    finally:
        cur.close()    

sql_deleteAcve = "DELETE FROM cve WHERE id=%s"
def resetCveInTbl(cve_id, conn):
    try:
        cur = conn.cursor()
        cur.execute(sql_deleteAcve, [cve_id])
        conn.commit()
    except Exception as err2:
        print("Error during update %s" %err2)
    finally:
        cur.close() 

sql_insertToCve = "INSERT into cve(id, publisheddate, lastmodifieddate, description) VALUES(%s, %s, %s, %s)"
def addToCveTbl(cve_id, publishedDate, lastModDate, description, conn):
    cur = conn.cursor()
    try:
        cur.execute(sql_insertToCve, (cve_id, publishedDate, lastModDate, description))     
        conn.commit()
    except Exception as exErr:
        print("Error executing SQL: %s"%exErr)
    finally:        
        cur.close()
    
sql_insertToBaseMetricV2 = "INSERT into basemetricv2 (cve_id, access_vector, base_score, exploitability_score, impact_score, severity_value, vector_string) VALUES (%s, %s, %s, %s,%s, %s, %s)"
def addToBaseMetricV2(cve_id, baseMetricV2, conn):
    if(baseMetricV2 is not None):
        cur = conn.cursor()
        cvssV2 = baseMetricV2.get("cvssV2")
        accessVector = cvssV2.get("accessVector")
        baseScore = cvssV2.get("baseScore")
        exploitabilityScore = baseMetricV2.get("exploitabilityScore")
        impactScore = baseMetricV2.get("impactScore")
        severity = baseMetricV2.get("severity")
        vectorString = cvssV2.get("vectorString")
     
        cur.execute(sql_insertToBaseMetricV2, (cve_id, accessVector, baseScore, exploitabilityScore, impactScore, severity, vectorString))
        conn.commit()
        cur.close()  

sql_insertToBaseMetricV3 = "INSERT into basemetricv3 (cve_id, attack_vector, base_score, base_severity, exploitability_score, impact_score, vector_string) VALUES (%s, %s, %s, %s,%s, %s, %s)"
def addToBaseMetricV3(cve_id, baseMetricV3, conn):
    if(baseMetricV3 is not None):
        cur = conn.cursor()
        cvssV3 = baseMetricV3.get("cvssV3")
        attackVector = cvssV3.get("attackVector")
        baseScore = cvssV3.get("baseScore")
        exploitabilityScore = baseMetricV3.get("exploitabilityScore")
        impactScore = baseMetricV3.get("impactScore")
        baseSeverity = cvssV3.get("baseSeverity")
        vectorString = cvssV3.get("vectorString")
        
        cur.execute(sql_insertToBaseMetricV3, (cve_id, attackVector, baseScore, baseSeverity, exploitabilityScore, impactScore, vectorString))
        conn.commit()
        cur.close()


sql_selectVendor = "SELECT id FROM public.vendorinfo where vendor_name=%s and product_name=%s"        
def getVendorID(vendorName, productName, conn):
    cur = conn.cursor()
    try:
        cur.execute(sql_selectVendor, (vendorName, productName))
    except Exception as err:
        print("Error yl %s" %err)
    
    if cur.rowcount > 0:    
        result = cur.fetchone()
        return result[0]
    else:
        return -1
    
sql_insertVendor = "INSERT INTO public.vendorinfo (vendor_name, product_name) values (%s, %s) RETURNING id"
def addVendorToDB(vendorName, productName, conn):
    cur = conn.cursor()
    try:
        cur.execute(sql_insertVendor, (vendorName, productName))
        conn.commit()
    except Exception as err:
        print("Error yl %s" %err)
        
    vendorId = cur.fetchone()[0]
    cur.close()
    return vendorId

sql_insertAffectedVendors = "INSERT INTO affectedvendors (cve_id, vendor_id, version_value) values (%s, %s, %s)"
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
            versions = product_item.get("version")
            for version_item in versions["version_data"]:
                version_value = version_item.get("version_value")
                cur = conn.cursor()
                cur.execute(sql_insertAffectedVendors, (cve_id, vendorId, version_value))
                conn.commit()
                cur.close()

sql_insertCPE = "INSERT INTO cpe (cve_id, cpe22uri, cpe23uri, version_start_excluding, version_start_including, version_end_excluding, version_end_including) values (%s, %s, %s, %s, %s, %s, %s)"                
def addToCpe(cve_id, configurations, conn):
    for node_item in configurations["nodes"]:
        if node_item["operator"] == "AND":
            if node_item.get("children") is None:
                for cpe_item in node_item["cpe"]:
                    processCpe(cve_id, cpe_item, conn)
            else:        
                for item in node_item["children"]:
                    if node_item.get("cpe") is not None: 
                        for cpe_item in item["cpe"]:
                            processCpe(cve_id, cpe_item, conn)
        else:
            if node_item.get("children") is None:
                if node_item.get("cpe") is not None:        
                    for cpe_item in node_item["cpe"]:
                        processCpe(cve_id, cpe_item, conn)
            else:
                for item in node_item["children"]:
                    for cpe_item in item["cpe"]:
                        processCpe(cve_id, cpe_item, conn)        

def processCpe(cve_id, cpe_item, conn):
    cur = conn.cursor()
    isVulnerable = cpe_item.get("vulnerable")
    if isVulnerable:
        cpe22Uri = cpe_item.get("cpe22Uri")
        cpe23Uri = cpe_item.get("cpe23Uri")
        cpeParts = cpe23Uri.split(":")
        vendorName = cpeParts[3]
        productName = cpeParts[4]
                
        vendorId = getVendorID(vendorName, productName, conn)
        if(vendorId == -1):
            #sometimes 'affects' has no data so need vendor info from cpe                    
            addVendorToDB(vendorName, productName, conn)
                
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
            print('Processing', fpath)
            #get a new connection for each file so we don't keep a connection open for too long
            dbConn = getDBConnection(dbConnectInfo)    
            processData(fpath, dbConn)
            if dbConn is not None:
                dbConn.close()
            
            print('Deleting processed file', fpath)    
            os.remove(fpath)    
    #delete downloaded files
    shutil.rmtree(cveDir, True, None)

def processData(fpath, conn):
    if conn is None:
        conn = getDBConnection(dbConnectInfo)
    with open(fpath, "r", encoding="utf8") as read_file:
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
            cveLastModDateInDB = getCveLastModDateFromTbl(cve_id, conn)
            if cveLastModDateInDB == -1:
                addToCveTbl(cve_id, publishedDate, lastModifiedDate, descriptionDataVal, conn)
            #skip cve in file if the one in the database is newer
            elif cveLastModDateInDB >= datetime.strptime(lastModifiedDate, "%Y-%m-%dT%H:%MZ"):
                continue
            else:
                #delete cve and re-process
                resetCveInTbl(cve_id, conn)
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

                    
def startProcess(url, dbConnInfo):
    if url is not None:
        jsonFeedUrl = url
    
    if dbConnInfo is not None:
        dbConnectInfo = dbConnInfo
        
    main()
    
    

    
# select count(distinct cve_id) as_num_of_cve, vendor_id, version_value from affectedvendors group by vendor_id, version_value order by as_num_of_cve desc limit 10;
# select count(distinct cve_id) as_num_of_cve, round(base_score) from basemetricv2 group by base_score order by base_score desc;
# select count(distinct cve_id) as_num_of_cve, round(base_score) from basemetricv3 group by base_score order by base_score desc;

