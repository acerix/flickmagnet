import os, os.path
import random
import string
import re
import time
import subprocess
from urllib.parse import quote
from datetime import date

import cherrypy
from cherrypy.lib.static import serve_file

# hide debug messages
cherrypy.log.screen = None

from mako.template import Template
from mako.lookup import TemplateLookup
templates_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
lookup = TemplateLookup(directories=[templates_dir])

# public trakers to add to magnet links so they start faster
default_torrent_trackers = [
  'udp://tracker.leechers-paradise.org:6969',
  'udp://zer0day.ch:1337',
  'udp://open.demonii.com:1337',
  'udp://tracker.coppersurfer.tk:6969',
  'udp://exodus.desync.com:6969',
  'http://pow7.com/announce',
  'http://denis.stalker.h3q.com:6969/announce'
]

# autodetect the video filename from the video release torrent
def detect_video_filename(info_hash, settings):

  mount_dir = os.path.join(settings['download_dir'], info_hash)

  # assume it's the biggest file
  find_result = subprocess.run(
    'find'
    + ' "' + mount_dir + '"'
    + ' -type f'
    + ' -printf "%s\\t%p\\n"'
    + ' | sort -n | tail -1 | awk \'{print $2}\'',
    stdout=subprocess.PIPE,
    shell=True,
    check=True
  )

  # @todo better way to strip garbage...
  return str(find_result.stdout).replace(mount_dir, '')[3:-3]


class RootController:

  # welcome

  @cherrypy.expose
  def index(self):

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  COUNT(*) torrent_count
FROM
  torrent
""")
    result = dbc.fetchone()

    return lookup.get_template("index.html").render(
      torrent_count = result['torrent_count']
    )

  # search

  @cherrypy.expose
  def search(self, q=None, genre=None):

    # @todo search for multiple params at the same time

    if q is not None and len(q):
      dbc = cherrypy.thread_data.db.execute("""

SELECT
  'movie' type,
  id,
  title,
  synopsis
FROM
  movie
WHERE
  title LIKE :query

UNION

SELECT
  'series' type,
  id,
  title,
  synopsis
FROM
  series
WHERE
  title LIKE :query

""", {
  'query': '%' + q + '%'
})
      results = dbc.fetchall()
      return lookup.get_template("results.html").render(results=results, q=q)

    if genre is not None:
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  *
FROM
  movie
WHERE
  EXISTS
  (
  SELECT
    *
  FROM
    movie_genre
  JOIN
    genre
      ON
        genre.id = movie_genre.genre_id
  WHERE
    genre.name = :genre_name
  AND
    movie_genre.movie_id = movie.id
  )
""", {
  'genre_name': genre
})
      results = dbc.fetchall()
      return lookup.get_template("results.html").render(results=results)

    return lookup.get_template("results.html").render(results=[])


  # browse movies

  @cherrypy.expose
  def movies(self):

    page_template = lookup.get_template("movies.html")

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie.*
FROM
  movie
ORDER BY
  movie.id DESC
LIMIT
  50
""")

    new_movies = dbc.fetchall()

    return page_template.render(
      title = "Movies",
      movies = new_movies
    )




  # browse tv shows

  @cherrypy.expose
  def tv(self):

    page_template = lookup.get_template("tv.html")

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  series_season_episode.*,
  series_season.number season_number,
  series.title series_title,
  series.id series_id
FROM
  series_season_episode
JOIN
  series_season
    ON
      series_season.id = series_season_episode.series_season_id
JOIN
  series
    ON
      series.id = series_season.series_id
ORDER BY
  series_season_episode.id DESC
LIMIT
  50
""")
    new_episodes = dbc.fetchall()

    return page_template.render(
      title = "TV Shows",
      episodes = new_episodes
    )



  # title info page

  @cherrypy.expose
  def title(self, title_id):

    # page_template = lookup.get_template("title.html")

    page_template = lookup.get_template("play.html")

    # find movie
    dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release.id,
  movie.title movie_title
FROM
  movie_release
JOIN
  movie
    ON
      movie.id = movie_release.movie_id
WHERE
  movie.id = ?
""", [
  title_id
])
    release = dbc.fetchone()

    if release:
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release_video.id,
  torrent.hash,
  movie_release_video.filename
FROM
  movie_release_video
JOIN
  torrent
    ON
      torrent.id = movie_release_video.torrent_id
WHERE
  movie_release_video.movie_release_id = ?
ORDER BY
  movie_release_video.id
""", [
  release['id']
])
      release_videos = dbc.fetchall()

      return page_template.render(
        title = release['movie_title'],
        title_id = int(title_id),
        release_videos = release_videos
      )


    # find series
    dbc = cherrypy.thread_data.db.execute("""
SELECT
  *
FROM
  series
WHERE
  id = ?
""", [
  title_id
])
    series = dbc.fetchone()

    if series:
      # @todo should not get all releases, only 1 per episode based on preferred video quality

      where_sql = """
  series_season.series_id = :series_id
"""
      query_params = {
        'series_id': series['id']
      }

      dbc = cherrypy.thread_data.db.execute("""
SELECT
  series_season_episode_release_video.id,
  torrent.hash,
  series_season_episode_release_video.filename
FROM
  series_season_episode_release_video
JOIN
  series_season_episode_release
    ON
      series_season_episode_release.id = series_season_episode_release_video.episode_release_id
JOIN
  series_season_episode
    ON
      series_season_episode.id = series_season_episode_release.episode_id
JOIN
  series_season
    ON
      series_season.id = series_season_episode.series_season_id
JOIN
  torrent
    ON
      torrent.id = series_season_episode_release_video.torrent_id
WHERE
  """ + where_sql + """
ORDER BY
  series_season.number,
  series_season_episode.number,
  series_season_episode_release_video.id
""", query_params)
      release_videos = dbc.fetchall()

      return page_template.render(
        title = series['title'],
        title_id = int(title_id),
        release_videos = release_videos
      )

    return 'Title not found'


  # video player

  @cherrypy.expose
  def play(self, title_id, season=None, episode=None):

    page_template = lookup.get_template("play.html")

    # find movie
    dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release.id,
  movie.title movie_title
FROM
  movie_release
JOIN
  movie
    ON
      movie.id = movie_release.movie_id
WHERE
  movie.id = ?
""", [
  title_id
])
    release = dbc.fetchone()

    if release:
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release_video.id,
  torrent.hash,
  movie_release_video.filename
FROM
  movie_release_video
JOIN
  torrent
    ON
      torrent.id = movie_release_video.torrent_id
WHERE
  movie_release_video.movie_release_id = ?
ORDER BY
  movie_release_video.id
""", [
  release['id']
])
      release_videos = dbc.fetchall()

      return page_template.render(
        title = release['movie_title'],
        title_id = int(title_id),
        release_videos = release_videos
      )


    # find series
    dbc = cherrypy.thread_data.db.execute("""
SELECT
  *
FROM
  series
WHERE
  id = ?
""", [
  title_id
])
    series = dbc.fetchone()

    if series:
      # @todo should not get all releases, only 1 per episode based on preferred video quality

      where_sql = """
  series_season.series_id = :series_id
"""
      query_params = {
        'series_id': series['id']
      }

      if season is not None:
        where_sql += """
AND
  series_season.number = :season
"""
        query_params['season'] = season

      if episode is not None:
        where_sql += """
AND
  series_season_episode.number = :episode
"""
        query_params['episode'] = episode

      dbc = cherrypy.thread_data.db.execute("""
SELECT
  series_season_episode_release_video.id,
  torrent.hash,
  series_season_episode_release_video.filename,
  torrent.hash title
FROM
  series_season_episode_release_video
JOIN
  series_season_episode_release
    ON
      series_season_episode_release.id = series_season_episode_release_video.episode_release_id
JOIN
  series_season_episode
    ON
      series_season_episode.id = series_season_episode_release.episode_id
JOIN
  series_season
    ON
      series_season.id = series_season_episode.series_season_id
JOIN
  torrent
    ON
      torrent.id = series_season_episode_release_video.torrent_id
WHERE
  """ + where_sql + """
ORDER BY
  series_season.number,
  series_season_episode.number,
  series_season_episode_release_video.id
""", query_params)
      release_videos = dbc.fetchall()

      title = series['title']
      if season is not None:
        title += ': Season ' + season.rjust(2, '0')

      if episode is not None:
        title += ', Episode ' + episode.rjust(2, '0')

      return page_template.render(
        title = series['title'],
        title_id = int(title_id),
        season = season,
        episode = episode,
        release_videos = release_videos
      )

    return 'Title not found'


  # generate an xspf playlist for the torrent video

  @cherrypy.expose
  def xspf(self, title_id, season=None, episode=None):

    # @todo deduplicate lookups in play()

    # find movie
    dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release.id,
  movie.title movie_title
FROM
  movie_release
JOIN
  movie
    ON
      movie.id = movie_release.movie_id
WHERE
  movie.id = ?
""", [
  title_id
])
    release = dbc.fetchone()

    release_videos = []

    if release:
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release_video.id,
  torrent.hash,
  movie_release_video.filename
FROM
  movie_release_video
JOIN
  torrent
    ON
      torrent.id = movie_release_video.torrent_id
WHERE
  movie_release_video.movie_release_id = ?
ORDER BY
  movie_release_video.id
""", [
  release['id']
])
      release_videos = dbc.fetchall()
      title = release['movie_title']

    else:

      # find series
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  *
FROM
  series
WHERE
  id = ?
""", [
  title_id
])
      series = dbc.fetchone()

      if series:
        # @todo should not get all releases, only 1 per episode based on preferred video quality

        where_sql = """
  series_season.series_id = :series_id
"""
        query_params = {
          'series_id': series['id']
        }

        if season is not None:
          where_sql += """
AND
  series_season.number = :season
"""
          query_params['season'] = season

        if episode is not None:
          where_sql += """
AND
  series_season_episode.number = :episode
"""
          query_params['episode'] = episode

        dbc = cherrypy.thread_data.db.execute("""
SELECT
  series_season_episode_release_video.id,
  torrent.hash,
  series_season_episode_release_video.filename,
  printf(
    '%s: Season %.2d Episode %.2d',
    series.title,
    series_season.number,
    series_season_episode.number
  ) title
FROM
  series_season_episode_release_video
JOIN
  series_season_episode_release
    ON
      series_season_episode_release.id = series_season_episode_release_video.episode_release_id
JOIN
  series_season_episode
    ON
      series_season_episode.id = series_season_episode_release.episode_id
JOIN
  series_season
    ON
      series_season.id = series_season_episode.series_season_id
JOIN
  series
    ON
      series.id = series_season.series_id
JOIN
  torrent
    ON
      torrent.id = series_season_episode_release_video.torrent_id
WHERE
  """ + where_sql + """
ORDER BY
  series_season.number,
  series_season_episode.number,
  series_season_episode_release_video.id
""", query_params)
      release_videos = dbc.fetchall()

      title = series['title']
      if season is not None:
        title += ': Season ' + season.rjust(2, '0')

      if episode is not None:
        title += ' Episode ' + episode.rjust(2, '0')

    page_template = lookup.get_template('videos.xspf')

    xspf_data = str.encode(page_template.render(
      title = title,
      url_base = ('http://%s:%d/' % (cherrypy.thread_data.settings['http_host'], cherrypy.thread_data.settings['http_port']) ),
      videos = release_videos
    ))

    playlist_filename = 'flickmagnet_' + re.sub('[^A-Za-z0-9 -_]+', '', title).replace(' ', '_') + '.xspf'

    cherrypy.response.headers['Content-Type'] = 'application/xspf+xml'
    cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="' + playlist_filename + '"'

    return xspf_data

  @cherrypy.expose
  def m3u(self, title_id, season=None, episode=None):

    # @todo deduplicate lookups in play()
    # @todo deduplicate playlist generators

    # find movie
    dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release.id,
  movie.title movie_title,
  movie.minutes_long
FROM
  movie_release
JOIN
  movie
    ON
      movie.id = movie_release.movie_id
WHERE
  movie.id = ?
""", [
  title_id
])
    release = dbc.fetchone()

    release_videos = []

    if release:
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  movie_release_video.id,
  torrent.hash,
  movie_release_video.filename,
  :seconds_long seconds_long
FROM
  movie_release_video
JOIN
  torrent
    ON
      torrent.id = movie_release_video.torrent_id
WHERE
  movie_release_video.movie_release_id = :release_id
ORDER BY
  movie_release_video.id
""", {
  'release_id': release['id'],
  'seconds_long': release['minutes_long'] * 60
})
      release_videos = dbc.fetchall()
      title = release['movie_title']

    else:

      # find series
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  *
FROM
  series
WHERE
  id = ?
""", [
  title_id
])
      series = dbc.fetchone()

      if series:
        # @todo should not get all releases, only 1 per episode based on preferred video quality

        where_sql = """
  series_season.series_id = :series_id
"""
        query_params = {
          'series_id': series['id']
        }

        if season is not None:
          where_sql += """
AND
  series_season.number = :season
"""
          query_params['season'] = season

        if episode is not None:
          where_sql += """
AND
  series_season_episode.number = :episode
"""
          query_params['episode'] = episode

        dbc = cherrypy.thread_data.db.execute("""
SELECT
  series_season_episode_release_video.id,
  torrent.hash,
  series_season_episode_release_video.filename,
  printf(
    '%s: Season %.2d Episode %.2d',
    series.title,
    series_season.number,
    series_season_episode.number
  ) title,
  (series_season_episode.minutes_long * 60) seconds_long
FROM
  series_season_episode_release_video
JOIN
  series_season_episode_release
    ON
      series_season_episode_release.id = series_season_episode_release_video.episode_release_id
JOIN
  series_season_episode
    ON
      series_season_episode.id = series_season_episode_release.episode_id
JOIN
  series_season
    ON
      series_season.id = series_season_episode.series_season_id
JOIN
  series
    ON
      series.id = series_season.series_id
JOIN
  torrent
    ON
      torrent.id = series_season_episode_release_video.torrent_id
WHERE
  """ + where_sql + """
ORDER BY
  series_season.number,
  series_season_episode.number,
  series_season_episode_release_video.id
""", query_params)
      release_videos = dbc.fetchall()

      title = series['title']
      if season is not None:
        title += ': Season ' + season.rjust(2, '0')

      if episode is not None:
        title += ' Episode ' + episode.rjust(2, '0')

    page_template = lookup.get_template('videos.m3u')

    video_data = str.encode(page_template.render(
      title = title,
      url_base = ('http://%s:%d/' % (cherrypy.thread_data.settings['http_host'], cherrypy.thread_data.settings['http_port']) ),
      videos = release_videos
    ))

    playlist_filename = 'flickmagnet_' + re.sub('[^A-Za-z0-9 -_]+', '', title).replace(' ', '_') + '.m3u'

    cherrypy.response.headers['Content-Type'] = 'audio/x-mpequrl'
    cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="' + playlist_filename + '"'

    return video_data




  # generate an xspf playlist every season/episode in a series

  @cherrypy.expose
  def series_xspf(self, entity_id):

    series_id = int(entity_id)

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  *
FROM
  series
WHERE
  id = ?
""", [
  series_id
])

    series = dbc.fetchone()

    page_template = lookup.get_template("series.xspf")

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  'Season ' || substr('0'||season.number, -2, 2) season_name,
  'Episode ' || substr('0'||episode.number, -2, 2) name,
  torrent.id release_id,
  episode.seconds_long
FROM
  torrent
JOIN
  episode
    ON
      :type_id_episode = torrent.entity_type_id
    AND
      episode.id = torrent.entity_id
JOIN
  season
    ON
      season.id = episode.season_id
WHERE
  season.series_id = :series_id
GROUP BY
  episode.id
ORDER BY
  season.number,
  episode.number
""", {
  'series_id': series_id,
  'type_id_episode': cherrypy.thread_data.settings['cached_tables']['entity_type']['episode']
})

    episodes = []

    for r in dbc.fetchall():
      episodes.append({
        'season_name': r['season_name'],
        'name': r['name'],
        'location': 'http://%s:%d/stream?release_id=%d' % (cherrypy.thread_data.settings['http_host'], cherrypy.thread_data.settings['http_port'], r['release_id']),
        'duration': 0 if r['seconds_long'] is None else r['seconds_long'] * 1000
      })

    if len(episodes) == 0:
      return 'no episodes found yet'

    #cherrypy.response.headers['Content-Type'] = 'text/plain'
    cherrypy.response.headers['Content-Type'] = 'application/xspf+xml'
    cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="series.xspf"'

    return str.encode(page_template.render(
      series_name = series['name'],
      episodes = episodes
    ))



  # stream a video

  @cherrypy.expose
  def stream(self, release_id):

    release_id = int(release_id)

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  torrent.*,
  magnet.btih,
  4 torrent_status
FROM
  torrent
JOIN
  magnet
    ON
      magnet.id = torrent.magnet_id
WHERE
  torrent.id = ?
""", [
  release_id
])

    torrent = dbc.fetchone()

    if torrent:

      # set torrent to start streaming
      dbc = cherrypy.thread_data.db.execute("""
UPDATE
  torrent
SET
  status_id = %d
WHERE
  id = %d
""" % (
  torrent['id']
))
      cherrypy.thread_data.db.commit()




  # import video list

  @cherrypy.expose
  def title_import(self, init=0, text=None):
    page_template = lookup.get_template("title_import.html")
    return page_template.render(
      init = init,
      text = text,
      import_stats = {
        'movies': 3,
        'shows': 13
      }
    )



  # recently watched videos

  @cherrypy.expose
  def history(self):
    page_template = lookup.get_template("history.html")
    return page_template.render(
      results = []
    )



  # daemon status info

  @cherrypy.expose
  def status(self):
    page_template = lookup.get_template("status.html")
    return page_template.render(
      status = 'alive'
    )



def start(settings, db_connect):

  cherrypy.config.update({
    'server.socket_host': str(settings['http_addr']),
    'server.socket_port': settings['http_port'],
    'engine.autoreload.on': False
  })

  ht_dir = settings['htdocs_dir']

  # 404 handler
  def error_page_404(status, message, traceback, version):

    # if the request is for a file in a torrent, try mounting the torrent
    m = re.search(r'/torrents/([0-9a-f]{40})(/.*)', cherrypy.request.path_info)
    if m is not None:
      info_hash = m.group(1)
      video_filename = m.group(2)[1:]
      mount_dir = os.path.join(settings['download_dir'], info_hash)

      # check that torrent exists in database
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  id
FROM
  torrent
WHERE
  hash = ?
""", [
  info_hash
])
      torrent = dbc.fetchone()

      if torrent is None:
        print('Torrent not found in database')
        return

      # create directory to mount
      if not os.path.isdir(mount_dir):
        os.mkdir(mount_dir)

      # if the torrent already contains files, assume the requested file is not in the torrent, return to 404
      if len( os.listdir(mount_dir) ):
        if len(video_filename):
          print('torrent already contains files')
          return

      else:
        torrent_params = ''

        for tracker in default_torrent_trackers:
          torrent_params = torrent_params + '&tr=' + quote(tracker)

        # mount torrent with btfs
        subprocess.Popen([
          'btfs',
          'magnet:?xt=urn:btih:' + info_hash + torrent_params,
          mount_dir
        ])

        # wait for files to appear (ie. metadata downloaded)
        while len( os.listdir(mount_dir) ) == 0:
          # print('Waiting for metadata...')
          time.sleep(1)


      # autodetect filename if blank
      if len(video_filename) == 0:
        video_filename = detect_video_filename(info_hash, cherrypy.thread_data.settings)
        video_url = cherrypy.request.path_info + video_filename
      else:
        video_url = cherrypy.request.path_info

      # reload to the file which now exists if it's in the torrent
      #cherrypy.HTTPRedirect(video_url)
      cherrypy.response.status = 302
      cherrypy.response.headers['Location'] = video_url
      cherrypy.response.body = None

  # set 404 handler
  cherrypy.config.update({'error_page.404': error_page_404})


  def connect(thread_index):
    # Create a connection and store it in the current thread
    cherrypy.thread_data.db = db_connect()

    # @todo better way to pass settings
    cherrypy.thread_data.settings = settings


  # Tell CherryPy to call "connect" for each thread, when it starts up
  cherrypy.engine.subscribe('start_thread', connect)

  # print('httpd starting on port', settings['http_port'])

  cherrypy.quickstart(
    RootController(),
    '/',
    {
      '/': {
        #'tools.sessions.on': True,
        'tools.staticdir.on': True,
        'tools.staticdir.dir': ht_dir
      },
      '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': os.path.join(ht_dir, 'favicon.ico')
      },
      '/robots.txt': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': os.path.join(ht_dir, 'robots.txt')
      },
      '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(ht_dir, 'static')
      },
      '/torrents': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': settings['download_dir'],
        'tools.staticdir.content_types' : {
          'VOB': 'video/mp4'
        }
      }
    }
  )

  os._exit(0)
