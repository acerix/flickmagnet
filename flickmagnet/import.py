#!/usr/bin/env python3

# based on https://github.com/acerix/media-torrent-db/blob/master/import.py
# @todo deduplicate

# config
import config

import sys
import csv
import os.path


# get arguments
if len(sys.argv) is not 2:
  print('Usage: ./import.py movies.csv')
  exit()
import_csv_filename = sys.argv[1]

# if the file doesn't exist, assume url and try downloading remote file
if not os.path.exists(import_csv_filename):
  import tempfile
  import urllib.request
  import_csv_url = import_csv_filename
  temp_file_handle, import_csv_filename = tempfile.mkstemp()
  urllib.request.urlretrieve(import_csv_url, import_csv_filename)

# database connection
db = config.db_connect()
db_cursor = db.cursor()


# find/add torrent
def get_torrent_id(import_row):
  db_cursor.execute("""
SELECT
  id
FROM
  torrent
WHERE
  hash = :info_hash
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  torrent
(
  hash
)
VALUES
(
  :info_hash
)
""", import_row)
    return db_cursor.lastrowid



# find the movie in the database from the row data otherwise add it, then return the database row id
def get_movie_id(import_row):
  # find existing by id
  db_cursor.execute("""
SELECT
  id
FROM
  movie
WHERE
  id = :id
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  movie
(
  id,
  title,
  synopsis,
  theater_release_year,
  theater_release_date,
  online_release_date,
  minutes_long,
  content_rating_id
)
VALUES
(
  :id,
  :title,
  :synopsis,
  :theater_release_year,
  :theater_release_date,
  :online_release_date,
  :minutes_long,
  (SELECT id FROM content_rating WHERE name = :content_rating)
)
""", import_row)
    movie_id = db_cursor.lastrowid

    for genre in import_row['genres'].split(','):
      if len(genre):
        db_cursor.execute("""
INSERT INTO
  movie_genre
(
  movie_id,
  genre_id
)
VALUES
(
  :movie_id,
  (SELECT id FROM genre WHERE name = :genre)
)
""", {
  'movie_id': movie_id,
  'genre': str(genre)
})

    return movie_id



# find/add release
def get_movie_release_id(import_row):
  db_cursor.execute("""
SELECT
  id
FROM
  movie_release
WHERE
  movie_id = :movie_id
AND
  release_format_id = (SELECT id FROM release_format WHERE name = :release_format)
AND
  video_quality_id = (SELECT id FROM video_quality WHERE name = :video_quality)
AND
  name = :release_name
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  movie_release
(
  movie_id,
  release_format_id,
  video_quality_id,
  name,
  created
)
VALUES
(
  :movie_id,
  (SELECT id FROM release_format WHERE name = :release_format),
  (SELECT id FROM video_quality WHERE name = :video_quality),
  :release_name,
  strftime('%s', 'now')
)
""", import_row)
    return db_cursor.lastrowid

# find/add release video
def get_movie_release_video_id(import_row):
  db_cursor.execute("""
SELECT
  id
FROM
  movie_release_video
WHERE
  movie_release_id = :movie_release_id
AND
  torrent_id = :torrent_id
AND
  filename = :video_filename
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  movie_release_video
(
  movie_release_id,
  torrent_id,
  filename
)
VALUES
(
  :movie_release_id,
  :torrent_id,
  :video_filename
)
""", import_row)
    return db_cursor.lastrowid





# find/add series
def get_series_id(import_row):
  # find existing by id
  db_cursor.execute("""
SELECT
  id
FROM
  series
WHERE
  id = :id
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  series
(
  id,
  title,
  synopsis,
  content_rating_id
)
VALUES
(
  :id,
  :series_title,
  :series_synopsis,
  (SELECT id FROM content_rating WHERE name = :content_rating)
)
""", import_row)
    series_id = db_cursor.lastrowid

    for genre in import_row['genres'].split(','):
      if len(genre):
        db_cursor.execute("""
INSERT INTO
  series_genre
(
  series_id,
  genre_id
)
VALUES
(
  :series_id,
  (SELECT id FROM genre WHERE name = :genre)
)
""", {
  'series_id': series_id,
  'genre': genre
})

    return series_id

# find/add series season
def get_series_season_id(import_row):
  # find existing by id
  db_cursor.execute("""
SELECT
  id
FROM
  series_season
WHERE
  series_id = :series_id
AND
  number = :season
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  series_season
(
  series_id,
  number
)
VALUES
(
  :series_id,
  :season
)
""", import_row)
    return db_cursor.lastrowid

# find/add series season episode
def get_series_season_episode_id(import_row):
  # find existing by id
  db_cursor.execute("""
SELECT
  id
FROM
  series_season_episode
WHERE
  series_season_id = :series_season_id
AND
  number = :episode
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  series_season_episode
(
  series_season_id,
  number,
  title,
  synopsis,
  minutes_long,
  release_date
)
VALUES
(
  :series_season_id,
  :episode,
  :title,
  :synopsis,
  :minutes_long,
  :release_date
)
""", import_row)
    return db_cursor.lastrowid

# find/add episode release
def get_series_season_episode_release_id(import_row):
  db_cursor.execute("""
SELECT
  id
FROM
  series_season_episode_release
WHERE
  episode_id = :series_season_episode_id
AND
  release_format_id = (SELECT id FROM release_format WHERE name = :release_format)
AND
  video_quality_id = (SELECT id FROM video_quality WHERE name = :video_quality)
AND
  name = :release_name
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  series_season_episode_release
(
  episode_id,
  release_format_id,
  video_quality_id,
  name,
  created
)
VALUES
(
  :series_season_episode_id,
  (SELECT id FROM release_format WHERE name = :release_format),
  (SELECT id FROM video_quality WHERE name = :video_quality),
  :release_name,
  strftime('%s', 'now')
)
""", import_row)
    return db_cursor.lastrowid

# find/add episode release video
def get_series_season_episode_release_video_id(import_row):
  db_cursor.execute("""
SELECT
  id
FROM
  series_season_episode_release_video
WHERE
  episode_release_id = :series_season_episode_release_id
AND
  torrent_id = :torrent_id
AND
  filename = :video_filename
""", import_row)
  db_row = db_cursor.fetchone()

  if db_row:
    return db_row['id']
  else:
    db_cursor.execute("""
INSERT INTO
  series_season_episode_release_video
(
  episode_release_id,
  torrent_id,
  filename
)
VALUES
(
  :series_season_episode_release_id,
  :torrent_id,
  :video_filename
)
""", import_row)
    return db_cursor.lastrowid




# open csv file and process each row
with open(import_csv_filename) as csv_file:
  csv_reader = csv.DictReader(csv_file)
  for row in csv_reader:

    # import torrent
    row['torrent_id'] = get_torrent_id(row)

    # import show
    if 'episode' in row and len(row['episode']):
      row['series_id'] = get_series_id(row)
      row['series_season_id'] = get_series_season_id(row)
      row['series_season_episode_id'] = get_series_season_episode_id(row)
      row['series_season_episode_release_id'] = get_series_season_episode_release_id(row)
      row['series_season_episode_release_video_id'] = get_series_season_episode_release_video_id(row)

    # import movie
    else:
      row['movie_id'] = get_movie_id(row)
      row['movie_release_id'] = get_movie_release_id(row)
      row['release_video_id'] = get_movie_release_video_id(row)


# close db
db.commit()
db_cursor.close()

