
# crawls the web find videos

# @todo needs error checking... what happens if offline or if imdb changes something?

# lists of titles on imdb.com
imdb_list_urls = [

    # public domain movies
    'http://www.imdb.com/list/ls003915205/?view=compact&sort=created:desc',
    'http://www.imdb.com/list/ls003915205/?view=compact&sort=created:desc&start=251',

    # newest dvd releases
    'http://www.imdb.com/sections/dvd/'

]

crawl_urls = [
    'https://kat.cr/tv/',
    'https://kat.cr/movies/'
]

import os
import time
import requests
import re
from bs4 import BeautifulSoup


def start(settings, db_connect):
    os._exit(0) # skip for now

    db = db_connect()
    #crawl_imdb_title(db, 111161)

    print('spiderd started')

    while True:

        for url in imdb_list_urls:
            crawl_imdb_list(db, url)

        time.sleep(60 * 60 * 6)

    os._exit(0)


# find html links to titles on imdb.com, add them to the database
def crawl_imdb_list(db, url):

    response = requests.get(url)

    for imdb_id in re.findall(r'[^>]href="/title/tt0*(\d+)', response.text):
        crawl_imdb_title(db, imdb_id)


# get details of the title from imdb.com, add it to the database
def crawl_imdb_title(db, imdb_id):

    response = requests.get('http://www.imdb.com/title/tt' + str(imdb_id).zfill(7) + '/')

    soup = BeautifulSoup(response.content, 'html.parser')

    # @todo handle titles which are not movies
    entity_type = 'movie'

    # find title, year
    title_tag = soup.title
    title_tag_match = re.match(r'(.*) \((\d{4})\) - IMDb', title_tag.string)
    title = title_tag_match.group(1)
    release_year = int(title_tag_match.group(2))

    # find duration
    duration_tag = soup.select_one('time[itemprop="duration"]')
    duration_tag_match = re.match(r'PT(\d+)M', duration_tag['datetime'])
    minutes_long = int(duration_tag_match.group(1))

    # find rating
    rating_tag = soup.select_one('span[itemprop="ratingValue"]')
    rating = float(rating_tag.string)

    # find synopsis
    synopsis_tag = soup.select_one('p[itemprop="description"]')
    synopsis = synopsis_tag.string.strip() if synopsis_tag.string else ""

    db.execute("""
INSERT OR REPLACE INTO
    """+entity_type+"""
(
    id,
    name,
    release_year,
    seconds_long,
    rating,
    synopsis
)
VALUES
(
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
)
""", [
    imdb_id,
    title,
    release_year,
    minutes_long * 60,
    rating,
    synopsis
])
    db.commit()

    # @todo get cover image
