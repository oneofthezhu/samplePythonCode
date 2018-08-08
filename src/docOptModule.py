"""Usage:
  processJsonCveFeeds.py setupDB [--db=<dbParams>]
  processJsonCveFeeds.py startProcess [--url=<jsonFeedUrl> --db=<dbParams>]
  processJsonCveFeeds.py -h | --help | --version
  
  Options:
  --url=<jsonFeedUrl>    Url with links to json.zip [default: https://nvd.nist.gov/vuln/data-feeds#JSON_FEED]
  --db=<dbParams>        DB connection string [default: dbname='postgres' user='postgres' host='localhost' password='password']
  -h --help              Show this screen
  --version              Show version
"""

import processJsonCveFeeds
from docopt import docopt

if __name__ == '__main__':
    arguments = docopt(__doc__, version='0.6.2')    
    if arguments['startProcess']:
        processJsonCveFeeds.startProcess(arguments['--url'], arguments['--db'])
    if arguments['setupDB']:
        processJsonCveFeeds.setupDB(arguments['--db'])    
