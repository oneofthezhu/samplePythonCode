import unittest
import psycopg2

class Test(unittest.TestCase):
    global postgresConn
    global postgresCursor
    global testConn
    global testCursor

    def setUp(self):
        print("Setting up")
        postgresConn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='password'")
        postgresConn.autocommit = True
        postgresCursor = postgresConn.cursor()
        postgresCursor.execute("SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.usename='postgres' AND pid <> pg_backend_pid();")            
        postgresCursor.execute("DROP DATABASE IF EXISTS test")
        postgresCursor.execute("CREATE DATABASE test")
        #postgresConn.close()
           
        #connect to new DB and create tables
        self.testConn = psycopg2.connect("dbname='test' user='postgres' host='localhost' password='password'")
        self.testCursor = self.testConn.cursor()
        sql_file = open('nvd_schema.sql', 'r')
        self.testCursor.execute(sql_file.read())
   
        sql_file.close()
        self.testConn.commit()
   
    def verifyCVE(self):
        self.testCursor.execute("SELECT * from cve")
        rows = self.testCursor.fetchall()
        self.assertEqual(self.testCursor.rowcount, 1)
        row = rows[0]
        self.assertEqual(row[0],"CVE-2011-5325")
        self.assertIn("Directory traversal vulnerability in the BusyBox impl", row[1])
        self.assertEqual("2017-08-07 17:29:00",row[2].strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEqual("2018-07-28 01:29:00",row[3].strftime("%Y-%m-%d %H:%M:%S"))
        
    def verifyCPE(self):
        self.testCursor.execute("SELECT * from cpe")
        rows = self.testCursor.fetchall()
        self.assertEqual(self.testCursor.rowcount, 1)
        row = rows[0]
        self.assertEqual(row[0],"CVE-2011-5325")
        self.assertEqual(row[1],"cpe:/a:busybox:busybox")
        self.assertEqual(row[2],"cpe:2.3:a:busybox:busybox:*:*:*:*:*:*:*:*")
        self.assertEqual(row[3],None)
        self.assertEqual(row[4],None)
        self.assertEqual(row[5],None)
        self.assertEqual(row[6],"1.21.1")
        
    def verifyBaseMetricv2(self):
        self.testCursor.execute("SELECT * from basemetricv2")
        rows = self.testCursor.fetchall()
        self.assertEqual(self.testCursor.rowcount, 1)
        row = rows[0]
        self.assertEqual(row[0],"CVE-2011-5325")
        self.assertEqual(row[1],"NETWORK")
        self.assertEqual(row[2],5.0)
        self.assertEqual(row[3],10.0)
        self.assertEqual(row[4],2.9)
        self.assertEqual(row[5],"(AV:N/AC:L/Au:N/C:N/I:P/A:N)")
        self.assertEqual(row[6],"MEDIUM")
        
    def testHappyPath(self):
        import processJsonCveFeeds
        #Need this so psycopg2 knows to look for tables in 'public' schema
        self.testCursor.execute("SET search_path TO public");
        processJsonCveFeeds.processData("justOneCVE.json", self.testConn )
        self.verifyCVE()
        self.verifyCPE()
        self.verifyBaseMetricv2()
    
    def testDuplicateCveID(self):
        import processJsonCveFeeds
        self.testCursor.execute("SET search_path TO public");         
        processJsonCveFeeds.processData("twoDupCVEs.json", self.testConn )
          
        self.testCursor.execute("SELECT * from cve where id='CVE-2011-5325'")
        rows = self.testCursor.fetchall()
        self.assertEqual(self.testCursor.rowcount, 1)
        row = rows[0]
        self.assertEqual("2018-08-08 01:29:00",row[3].strftime("%Y-%m-%d %H:%M:%S"))
                 
        self.testCursor.execute("SELECT base_score from basemetricv2 where cve_id='CVE-2011-5325'")
        rows = self.testCursor.fetchall()
        self.assertEqual(self.testCursor.rowcount, 1)
        row = rows[0]
        self.assertEqual(2.0,row[0])
    
    #These should not throw exceptions    
    def testComplicatedCPEconfig(self):
        import processJsonCveFeeds
        self.testCursor.execute("SET search_path TO public");
        processJsonCveFeeds.processData("justOneCVEComplicatedConfig.json", self.testConn )
         
    def testJustOneCVE_AND_OR_CPE(self):      
        import processJsonCveFeeds
        self.testCursor.execute("SET search_path TO public");
        processJsonCveFeeds.processData("justOneCVE_AND_OR_CPE.json", self.testConn )
         
    def testOneCVEallORcpe(self):
        import processJsonCveFeeds
        self.testCursor.execute("SET search_path TO public");
        processJsonCveFeeds.processData("justOneCVEallORCPE.json", self.testConn )
             
    def tearDown(self):
        self.testCursor.close()
        self.testConn.close()


if __name__ == "__main__":
    unittest.main()