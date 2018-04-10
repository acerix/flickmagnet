import os, os.path
import random
import string
import time
from datetime import date

import cherrypy
from cherrypy.lib.static import serve_file

# hide debug messages
cherrypy.log.screen = None


from mako.template import Template
from mako.lookup import TemplateLookup
templates_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
lookup = TemplateLookup(directories=[templates_dir])


class RootController:


  # welcome

  @cherrypy.expose
  def index(self):
    return lookup.get_template("index.html").render()

  # search

  @cherrypy.expose
  def search(self, q=None, genre=None):

    # @todo search for multiple params at the same time

    if q is not None and len(q):
      dbc = cherrypy.thread_data.db.execute("""
SELECT
  *
FROM
  movie
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
  series_season_episode.number season_number,
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

    page_template = lookup.get_template("title.html")

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  id,
  title
FROM
  movie
WHERE
  id = ?
""", [
  title_id
])
    movie = dbc.fetchone()

    if movie:

      return page_template.render(
        title_id = title_id,
        title = movie['title'],
      )

    return 'title not found'





  # video player

  @cherrypy.expose
  def play(self, title_id):

    page_template = lookup.get_template("play.html")

    dbc = cherrypy.thread_data.db.execute("""
SELECT
  id
FROM
  movie
WHERE
  id = ?
""", [
  title_id
])
    movie = dbc.fetchone()

    if movie:

      return page_template.render(
        title = 'Watch Video',
        movie_id = movie['id'],
        title_id = title_id,
        video_url = 'https://www.quirksmode.org/html5/videos/big_buck_bunny.mp4'
      )


    return 'no magnets found'


  # stream a video

  @cherrypy.expose
  def stream(self, magnet_file_id):

    magnet_file_id = int(magnet_file_id)



    dbc = cherrypy.thread_data.db.execute("""
SELECT
  magnet_file.*,
  magnet.btih,
  4 torrent_status
FROM
  magnet_file
JOIN
  magnet
    ON
      magnet.id = magnet_file.magnet_id
WHERE
  magnet_file.id = ?
""", [
  magnet_file_id
])

    magnet_file = dbc.fetchone()

    if magnet_file:

      # set torrent to start streaming
      dbc = cherrypy.thread_data.db.execute("""
UPDATE
  magnet_file
SET
  status_id = %d
WHERE
  id = %d
""" % (
  magnet_file['id']
))
      cherrypy.thread_data.db.commit()




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
      }
    }
  )

  os._exit(0)
