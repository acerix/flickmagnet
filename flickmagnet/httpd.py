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
    def search(self, q=None, tag=[]):

        sql_movie_filter = sql_episode_filter = "1"

        query_params = {
            'type_id_movie': cherrypy.thread_data.settings['cached_tables']['entity_type']['movie'],
            'type_id_episode': cherrypy.thread_data.settings['cached_tables']['entity_type']['episode']
        }

        deep_search_running = False

        if q is not None and len(q):

            # tell spiderd to find titles with this match
            dbc = cherrypy.thread_data.db.execute("""
SELECT
    *
FROM
    search_query
WHERE
    query = ?
""", [
    q
])
            cherrypy.thread_data.db.commit()

            # first time query, spider it
            if dbc.fetchone() is None:

                deep_search_running = True

                # tell spiderd to find titles with this match
                cherrypy.thread_data.db.execute("""
INSERT OR IGNORE INTO
    search_query
(
    query
)
VALUES
(
    ?
)
""", [
    q
    ])
                cherrypy.thread_data.db.commit()

            query = '%'+q+'%'
            sql_movie_filter += " AND movie.name LIKE :query "
            sql_episode_filter += " AND series.name LIKE :query "
            query_params['query'] = query

        # for one tag, convert to list so it's the same as multiple tags
        if isinstance(tag, str):
            tag = [tag]

        if isinstance(tag, list) and len(tag):
            for k,v in enumerate(tag):
                sql_movie_filter += """
    AND EXISTS
(
SELECT
    *
FROM
    movie_tag
JOIN
    tag
        ON
            tag.id = movie_tag.tag_id
        AND
            tag.name = :tag_"""+str(k)+"""_name
WHERE
    movie_tag.movie_id = movie.id
)
"""
                query_params['tag_'+str(k)+'_name'] = v

        dbc = cherrypy.thread_data.db.execute("""
SELECT
    type,
    id,
    name,
    release_year,
    synopsis
FROM

(

SELECT
    'movie' type,
    movie.id,
    movie.name,
    movie.release_year,
    movie.synopsis
FROM
    movie
WHERE
    """ + sql_movie_filter + """
AND
    EXISTS
(
SELECT
    *
FROM
    magnet_file
WHERE
    magnet_file.entity_type_id = :type_id_movie
AND
    magnet_file.entity_id = movie.id
)

UNION

SELECT
    'episode' type,
    episode.id,
    series.name || ' S' ||  season.number || ' E' || episode.number name,
    NULL release_year,
    episode.synopsis
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
    """ + sql_episode_filter + """
AND
    EXISTS
(
SELECT
    *
FROM
    magnet_file
WHERE
    magnet_file.entity_type_id = :type_id_episode
AND
    magnet_file.entity_id = episode.id
)

)

ORDER BY
    id DESC
""", query_params)

        results = dbc.fetchall()

        return lookup.get_template("results.html").render(results=results, deep_search_running=deep_search_running)


    # browse movies

    @cherrypy.expose
    def movies(self):

        page_template = lookup.get_template("movies.html")

        dbc = cherrypy.thread_data.db.execute("""
SELECT
    movie.*
FROM
    movie
WHERE
(
    movie.release_year < %d
OR
    movie.public_domain = 1
)
AND
    EXISTS
(
SELECT
    *
FROM
    magnet_file
WHERE
    magnet_file.entity_type_id = %d
AND
    magnet_file.entity_id = movie.id
)
ORDER BY
    movie.id DESC
""" % (
    date.today().year + 1 - cherrypy.thread_data.settings['copyright_length'],
    cherrypy.thread_data.settings['cached_tables']['entity_type']['movie']
))

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
    episode.*,
    season.number season_number,
    series.name series_name
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
    EXISTS
(
SELECT
    *
FROM
    magnet_file
WHERE
    magnet_file.entity_type_id = %d
AND
    magnet_file.entity_id = episode.id
)
ORDER BY
    episode.id DESC
""" % (
    cherrypy.thread_data.settings['cached_tables']['entity_type']['episode']
))
        new_episodes = dbc.fetchall()

        return page_template.render(
            title = "TV Shows",
            episodes = new_episodes
        )





    # video player

    @cherrypy.expose
    def play(self, entity_type, entity_id):

        entity_type_id = cherrypy.thread_data.settings['cached_tables']['entity_type'][entity_type]

        page_template = lookup.get_template("play.html")

        dbc = cherrypy.thread_data.db.execute("""
SELECT
    id
FROM
    magnet_file
WHERE
    entity_type_id = ?
AND
    entity_id = ?
""", [
    entity_type_id,
    entity_id
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
    cherrypy.thread_data.settings['cached_tables']['magnet_file_status']['start watching'],
    magnet_file['id']
))
            cherrypy.thread_data.db.commit()

            return page_template.render(
                entity_id = entity_id,
                magnet_file_id = magnet_file['id']
            )


        return 'no magnets found'



    # generate an xspf playlist for the magnet_file video

    @cherrypy.expose
    def xspf(self, magnet_file_id):

        magnet_file_id = int(magnet_file_id)

        dbc = cherrypy.thread_data.db.execute("""
SELECT
    *
FROM
    magnet_file
WHERE
    id = ?
""", [
    magnet_file_id
])

        magnet_file = dbc.fetchone()

        page_template = lookup.get_template("magnet_file.xspf")

        location = 'http://%s:%d/stream?magnet_file_id=%d' % (cherrypy.thread_data.settings['http_host'], cherrypy.thread_data.settings['http_port'], magnet_file_id)

        # @todo actual duration
        duration = 0

        cherrypy.response.headers['Content-Type'] = 'application/xspf+xml'
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="flick.xspf"'

        return str.encode(page_template.render(location=location, duration=duration))


    # stream a video

    @cherrypy.expose
    def stream(self, magnet_file_id):

        magnet_file_id = int(magnet_file_id)

        # wait for torrent metadata to be downloaded and video file to be located
        for n in range(30):

            dbc = cherrypy.thread_data.db.execute("""
SELECT
    magnet_file.*,
    4 torrent_status
FROM
    magnet_file
WHERE
    id = ?
""", [
    magnet_file_id
])

            magnet_file = dbc.fetchone()

            if len(magnet_file['filename']):
                break

            print('waiting for torrent metadata')
            time.sleep(n)




        video_filename = os.path.join(cherrypy.thread_data.settings['download_dir'], magnet_file['filename'])

        # wait for video file to start downloading
        for n in range(30):
            if os.path.isfile(video_filename):
                break
            print('waiting for video to start downloading')
            time.sleep(n)


        cherrypy.response.headers['Content-Type'] = 'video/mpeg'
        cherrypy.response.headers['Content-Length'] = os.path.getsize(video_filename)


        # if download is complete, output as a static file
        # if finished or seeding:
        #if magnet_file['torrent_status'] == 4 or magnet_file['torrent_status'] == 5:
        return serve_file(video_filename, content_type='video/mpeg')



        # @todo need to accept ranges so video players can seek
        #cherrypy.response.headers['Accept-Ranges'] = 'bytes'


        # for now, this will never be reached... we just send zeroes to the browser for any parts not downloaded yet

        # torrent_handle::file_progress   ?

        # switch to streaming mode
        cherrypy.response.stream = True

        #chunk_size = magnet_file.chunk_size

        # yields chunks of data or sleeps until data is available
        def video_stream_or_block():
            # @todo start at beginning or range
            # @todo foreach (block): if (downloaded) yield, else sleep
            yield "Hello, "
            yield "world"

        return video_stream_or_block()




def start(settings, db_connect):

    cherrypy.config.update({
        'server.socket_host': settings['http_addr'],
        'server.socket_port': settings['http_port'],
        'engine.autoreload.on': False
    })

    cherrypy.server.socket_host = settings['http_addr']

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
            '/t': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': settings['thumbnail_dir']
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
