# torspider
It does things that crawl Tor.

Initial ideas inspired by terrible jokes on Discord about Tor analytics.
Lots of help with not reinventing the code for the crawling wheel comes from [this crawler](https://github.com/dirtyfilthy/freshonions-torscraper).

Licence is AGPL.

## Notes
* `docker-compose run --rm spider python init_db.py` - Init the DB
* `docker-compose up --scale spider=4 -d` brings some nice multispider crawling 
* [Rebloom](http://rebloom.io/) is a required Redis module for duplicate URL filtering.
