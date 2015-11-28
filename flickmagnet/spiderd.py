
# crawls the web find videos

# @todo needs error checking... what happens if offline or if imdb changes something?

# lists of titles on imdb.com, these are retrieved on the first run
imdb_list_urls = [

    # public domain movies
    'http://www.imdb.com/list/ls003915205/?view=compact&sort=created:desc',
    'http://www.imdb.com/list/ls003915205/?view=compact&sort=created:desc&start=251'

]

# lists of new released on imdb.com updated once a day
imdb_update_urls = [

    # new dvd releases
    'http://www.imdb.com/sections/dvd/'

]

# pages with magnets or torrents to scrape
crawl_urls = [
    'https://kat.cr/tv/',
    'https://kat.cr/movies/'
]

# urls to query for a list of magnets/torrents based on imdb id %d
search_urls = [
    'https://kat.cr/usearch/imdb%%3A%d/?field=seeders&sorder=desc'
]

# urls to query for a list of magnets/torrents based on tv series name and season number
season_search_urls = [
    'https://kat.cr/usearch/%s%%20season%%20%d/?field=seeders&sorder=desc'
]

# urls to query for a list of imdb id's for a keyword search query %s
title_search_urls = [
    'http://www.imdb.com/find?q=%s'
]

import os
import time
import requests
import re
import urllib
import sys
from bs4 import BeautifulSoup

from multiprocessing import Process

# returns true if the Internet is working
def internet_works(requests_session):
    response = requests_session.get('http://flickmag.net/')
    return len(response.text) > 0



def start(settings, db_connect):

    db = db_connect()
    requests_session = requests.Session()

    print('spiderd started')

    while not internet_works(requests_session):
        print('spiderd: error connecting to Internet, trying again in 60 seconds')
        time.sleep(60)

    if settings['first_run']:

        # start by adding Wizard of Oz as a demo that works right away
        crawl_imdb_title(settings, db, requests_session, 16544, 1, True)



    # only spider public domain movies one time
    dbc = db.execute("""
SELECT
    COUNT(*)
FROM
    movie
WHERE
    public_domain = 1
""")
    existing_publicdomain_movie_count = dbc.fetchone()[0]

    if existing_publicdomain_movie_count < 2:

        # add imdb's public domain movies in a new process
        spiderd_process = Process(target=crawl_public_domain_movies, args=(db, requests.Session()))
        spiderd_process.start()

    loop_number = 0

    while True:


        # every second
        # @todo running every second find search results faster, but for production it should sleep longer when idle to save resources
        propagate_queries(settings, db, requests_session)

        # finds magnets for newly added episodes
        magnetize_new_episodes(settings, db, requests_session)

        # finds magnets for newly added movies
        magnetize_new_movies(settings, db, requests_session)

        # every 30 seconds
        if 0 == loop_number % 30:

            if not internet_works(requests_session):
                print('spiderd: lost connection to Internet, sleeping for 10 minutes')
                time.sleep(600)


        # every 12 hours
        if 0 == loop_number % 43200:

            # add new dvd releases
            for url in imdb_update_urls:
                crawl_imdb_list(settings, db, requests_session, url)


        time.sleep(1)
        loop_number += 1

    print('spiderd ended')

    os._exit(0)


# find html links to titles on imdb.com, add them to the database
def crawl_imdb_list(settings, db, requests_session, url, public_domain=0):

    response = requests_session.get(url)
    print('crawling',url)

    for imdb_id in set(re.findall(r'[^>]href="/title/tt0*(\d+)', response.text)):
        crawl_imdb_title(settings, db, requests_session, imdb_id, public_domain)


# get details of the title from imdb.com, add it to the database
def crawl_imdb_title(settings, db, requests_session, imdb_id, public_domain=0, replace_existing=False):

    imdb_id = int(imdb_id)

    # skip existing
    dbc = db.execute("""
SELECT
    id
FROM
    movie
WHERE
    id = :imdb_id
UNION
SELECT
    id
FROM
    series
WHERE
    id = :imdb_id
UNION
SELECT
    id
FROM
    episode
WHERE
    id = :imdb_id
""", {
    'imdb_id': imdb_id
})
    existing_entity = dbc.fetchone()

    if existing_entity is not None and not replace_existing:
        return

    print('add imdb id:', imdb_id)

    response = requests_session.get('http://www.imdb.com/title/tt' + str(imdb_id).zfill(7) + '/')

    soup = BeautifulSoup(response.content, 'html.parser')

    # default to movie
    entity_type = 'movie'

    # if this is a tv series, find latest season
    latest_season_tag = soup.select_one('div.seasons-and-year-nav > div:nth-of-type(3) > a')
    if latest_season_tag:
        entity_type = 'series'
        if 'Unknown' == latest_season_tag.string:
            latest_season = 0
        else:
            latest_season = int(latest_season_tag.string)

    # find title, year
    title_tag = soup.title
    title_tag_match = re.match(r'(.*) \([^)]*(\d{4})[^)]*\) - IMDb', title_tag.string)

    if title_tag_match is None or title_tag_match.group(1) is None:
        return False
    title = title_tag_match.group(1)

    if title_tag_match.group(2) is not None:
        release_year = int(title_tag_match.group(2))
    else:
        release_year = 0

    # find duration
    duration_tag = soup.select_one('time[itemprop="duration"]')
    if duration_tag:
        duration_tag_match = re.match(r'PT(\d+)M', duration_tag['datetime'])
        minutes_long = int(duration_tag_match.group(1))
    else:
        minutes_long = 0

    # find rating
    rating_tag = soup.select_one('span[itemprop="ratingValue"]')
    if rating_tag:
        rating = float(rating_tag.string)
    else:
        rating = 0


    # find synopsis
    synopsis_tag = soup.select_one('p[itemprop="description"]')
    synopsis = synopsis_tag.string.strip() if synopsis_tag.string else ""


    if 'movie'==entity_type:
        db.execute("""
INSERT OR REPLACE INTO
    """+entity_type+"""
(
    id,
    name,
    release_year,
    seconds_long,
    rating,
    synopsis,
    public_domain
)
VALUES
(
    ?,
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
    synopsis,
    public_domain
])


    if 'series'==entity_type:
        db.execute("""
INSERT OR REPLACE INTO
    """+entity_type+"""
(
    id,
    name,
    rating,
    synopsis
)
VALUES
(
    ?,
    ?,
    ?,
    ?
)
""", [
    imdb_id,
    title,
    rating,
    synopsis
])

    db.commit()


    if 'series'==entity_type:
        for season_number in range(1, latest_season):
            print ('season', season_number)
            dbc = db.execute("""
INSERT OR IGNORE INTO
    season
(
    series_id,
    number
)
VALUES
(
    ?,
    ?
)
""", [
    imdb_id,
    season_number
])
            db.commit()

            season_id = dbc.lastrowid

            season_response = requests_session.get('http://www.imdb.com/title/tt' + str(imdb_id).zfill(7) + '/episodes?season='+str(season_number))

            season_soup = BeautifulSoup(season_response.content, 'html.parser')

            # find episodes for this season
            for episode_url in season_soup.select('div.eplist > div.list_item > div.image > a'):

                episode_imdb_id_match = re.match(r'/title/tt0*(\d+)/\?ref_=ttep_ep(\d+)', episode_url['href'])
                db.execute("""
INSERT OR IGNORE INTO
    episode
(
    id,
    season_id,
    number
)
VALUES
(
    ?,
    ?,
    ?
)
""", [
    episode_imdb_id_match.group(1),
    season_id,
    episode_imdb_id_match.group(2)
])
            db.commit()

    entity_id = str(imdb_id)

    # find and add genres
    for genre in soup.select('span[itemprop="genre"]'):
        db.execute("""
INSERT OR IGNORE INTO
    """+entity_type+"""_tag
(
    """+entity_type+"""_id,
    tag_id
)
VALUES
(
    ?,
    (SELECT id FROM tag WHERE name = ?)
)
""", [
    entity_id,
    genre.string
])
        db.commit()




    # cover image
    cover_image_filename = os.path.join(settings['thumbnail_dir'], str(imdb_id)+'.jpg')

    if not os.path.exists(cover_image_filename):

        # small
        cover_img_tag = soup.select_one('img[width="214"]')

        # large
        #cover_img_tag = soup.select_one('meta[property="og:image"]')
        #cover_img_url = cover_img_tag['content']

        # save thumbnail
        if cover_img_tag:
            cover_img_url = cover_img_tag['src']
            cover_img_response = requests_session.get(cover_img_url)
            cover_img_f = open(cover_image_filename, 'wb')
            cover_img_f.write(cover_img_response.content)
            cover_img_f.close()



# try to find magnets for newly added movies
def magnetize_new_movies(settings, db, requests_session):

    entity_statuses = settings['cached_tables']['entity_status']

    # find new movies
    dbc = db.execute("""
SELECT
    id
FROM
    movie
WHERE
    movie.status_id = :status_id
""", {
    'status_id': entity_statuses['new']
})
    for r in dbc.fetchall():
        magnets_found = 0

        for search_url in search_urls:

            print(search_url % (r['id']))

            results_response = requests_session.get(search_url % (r['id']))
            #results_soup = BeautifulSoup(results_response.content, 'html.parser')

            # loop through magnet links
            for btih in set(re.findall(r'btih:([0-9a-fA-F]{40})', results_response.text)):

                btih = btih.upper()

                #print(btih)

                # add magnet
                db.execute("""
INSERT OR IGNORE INTO
    magnet
(
    btih
)
VALUES
(
    ?
)
""", [
    btih
])
                db.commit()

                # lookup magnet id
                dbc = db.execute("""
SELECT
    id
FROM
    magnet
WHERE
    btih = '%s'
""" % (
    btih
))

                magnet = dbc.fetchone()

                # add magnet file
                db.execute("""
INSERT INTO
    magnet_file
(
    person_id,
    quality,
    filename,
    entity_type_id,
    entity_id,
    magnet_id
)
VALUES
(
    0,
    0,
    '',
    2,
    ?,
    ?
)
""", [
    r['id'],
    magnet['id']
])
                db.commit()

                magnets_found += 1

                # stop after finding one
                if magnets_found > 0:
                    break

            # stop after finding one
            if magnets_found > 0:
                break

        #print('mf:', magnets_found)

        db.execute("""
UPDATE
    movie
SET
    status_id = %d
WHERE
    id = %d
""" % (
    entity_statuses['magnetized'] if magnets_found else entity_statuses['unavailable'],
    r['id']
))
        db.commit()



# try to find magnets for newly added tv episodes
def magnetize_new_episodes(settings, db, requests_session):

    entity_statuses = settings['cached_tables']['entity_status']

    # find new episode
    dbc = db.execute("""
SELECT
    episode.id
    ,episode.number
    ,season.id season_id
    ,season.number season_number
    ,series.name series_name
FROM
    episode
JOIN
    season
        ON
            season.id = episode.season_id
JOIN
    series
        ON
            series.id = season.series_id
WHERE
    episode.status_id = :status_id
""", {
    'status_id': entity_statuses['new']
})
    for r in dbc.fetchall():

        magnets_found = 0

        for search_url in season_search_urls:

            # python3
            if sys.version_info >= (3, 0):
                results_response = requests_session.get(search_url % (urllib.parse.quote(r['series_name']), r['season_number']))

            # python2
            else:
                results_response = requests_session.get(search_url % (urllib.parse.quote(r['series_name']), r['season_number']))

            # loop through magnet links
            for btih in set(re.findall(r'btih:([0-9a-fA-F]{40})', results_response.text)):

                btih = btih.upper()

                #print(btih)

                # add magnet
                db.execute("""
INSERT OR IGNORE INTO
    magnet
(
    btih
)
VALUES
(
    '%s'
)
""" % (
    btih
))
                db.commit()

                # lookup magnet id
                dbc = db.execute("""
SELECT
    id
FROM
    magnet
WHERE
    btih = '%s'
""" % (
    btih
))

                magnet = dbc.fetchone()

                # why is this sometimes None?
                if magnet is not None:

                    # add magnet files
                    db.execute("""
INSERT INTO
    magnet_file
(
    person_id,
    quality,
    filename,
    entity_type_id,
    entity_id,
    magnet_id
)

SELECT
    0 person_id,
    0 quality,
    '' filename,
    1 entity_type_id,
    episode.id entity_id,
    %d magnet_id
FROM
    episode
WHERE
    episode.season_id = %d
""" % (
    magnet['id'],
    r['season_id']
))

                    db.commit()

                    magnets_found += 1


                # stop after finding one
                if magnets_found > 0:
                    break

            # stop after finding one
            if magnets_found > 0:
                break

        #print('mf:', magnets_found)

        db.execute("""
UPDATE
    episode
SET
    status_id = ?
WHERE
    episode.season_id = ?
""", [
    entity_statuses['magnetized'] if magnets_found else entity_statuses['unavailable'],
    r['season_id']
])
        db.commit()




# lookup recent search terms and add matching imdb titles
def propagate_queries(settings, db, requests_session):
    #print('propagate')

    entity_statuses = settings['cached_tables']['entity_status']

    # find new movies
    dbc = db.execute("""
SELECT
    *
FROM
    search_query
WHERE
    status_id = 1
""")
    for r in dbc.fetchall():

        db.execute("""
UPDATE
    search_query
SET
    status_id = 50
WHERE
    id = %d
""" % (
    r['id']
))
        db.commit()

        for title_search_url in title_search_urls:

            titles_found = 0

            print(title_search_url % r['query'])

            results_response = requests_session.get(title_search_url % r['query'])

            # loop through imdb id's
            for imdb_id in set(re.findall(r'/title/tt([0-9]{1,7})', results_response.text)):

                imdb_id = int(imdb_id)

                #print(imdb_id)

                crawl_imdb_title(settings, db, requests_session, imdb_id)

                titles_found += 1



        db.execute("""
UPDATE
    search_query
SET
    status_id = %d
WHERE
    id = %d
""" % (
    51 if titles_found else 52,
    r['id']
))
        db.commit()






# crawl public domain movies from imdb
def crawl_public_domain_movies(settings, db, requests_session):

    print('Initilializing database with public domain movies from imdb')

    for url in imdb_list_urls:
        crawl_imdb_list(settings, db, requests_session, url, 1)
