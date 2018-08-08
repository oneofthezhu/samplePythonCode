# README

Please execute "docOptModule.py" to see available commands.

The database must exists before running this program.
After confirming the database exists, please run "processJsonCveFeeds.py setupDB [--db=<dbParams>]" to create all the necessary tables.
And finally, run "processJsonCveFeeds.py startProcess [--url=<jsonFeedUrl> --db=<dbParams>]" to start parsing the cves and storing the data in the database.