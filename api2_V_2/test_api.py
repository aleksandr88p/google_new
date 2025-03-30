from page_requester import GoogleRequester
from page_parser import DekstopScrape
import asyncio
import json

requester = GoogleRequester()
scraper = DekstopScrape()

answer = asyncio.run(requester.search_google_async(query='burger', num=10))


d = asyncio.run(scraper.make_json(answer['html']))
print(json.dumps(d, indent=4))