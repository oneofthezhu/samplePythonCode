"""Usage:
  ProcessJsonCveFeeds.py top <howMany>
  ProcessJsonCveFeeds.py breakdown <score>
  ProcessJsonCveFeeds.py startProcess [--url=<jsonFeedUrl> --db=<dbParams>]
  ProcessJsonCveFeeds.py -h | --help | --version
  
  Options:
  -h --help              Show this screen
  --version              Show version
  --url=<jsonFeedUrl>    Url with links to json.zip [default: https://nvd.nist.gov/vuln/data-feeds#JSON_FEED]
  --db=<dbParams>        DB connection string [default: dbname='postgres' user='postgres' host='localhost' password='password']
"""

import ProcessJsonCveFeeds
from docopt import docopt


if __name__ == '__main__':
    arguments = docopt(__doc__, version='0.6.2')
    #print(arguments) #uncomment for debugging
    if arguments['top']:
        print("We gonno print " + arguments['<howMany>'] + " most vulnerable products!!!11!")
    if arguments['breakdown']:
        print("We gonno show breakdown for CVEs with score " + arguments['<score>'])
    if arguments['startProcess']:
        ProcessJsonCveFeeds.startProcess(arguments['--url'], arguments['--db'])
        
