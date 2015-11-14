import os, os.path
import random
import string
import time

import cherrypy

# hide debug messages
cherrypy.log.screen = None


from mako.template import Template
from mako.lookup import TemplateLookup
templates_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
lookup = TemplateLookup(directories=[templates_dir])


class RootController:


    # index of all content

    @cherrypy.expose
    def index(self, name=None):

        page_template = lookup.get_template("index.html")

        dbc = cherrypy.thread_data.db.execute("""
SELECT
    movie.*
FROM
    movie
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
    magnet_file.entity_id = movie.id
)
ORDER BY
    movie.id DESC
LIMIT
    30
""" % (
    cherrypy.thread_data.settings['cached_tables']['entity_type']['movie']
))

        new_movies = dbc.fetchall()

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
LIMIT
    30
""" % (
    cherrypy.thread_data.settings['cached_tables']['entity_type']['episode']
))
        new_episodes = dbc.fetchall()

        return page_template.render(
            title = "Index",
            movies = new_movies,
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
    *
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

        #return video_filename


        cherrypy.response.headers['Content-Type'] = 'video/mpeg'
        cherrypy.response.headers['Content-Length'] = os.path.getsize(video_filename)

        # @todo need to accept ranges so video players can seek
        #cherrypy.response.headers['Accept-Ranges'] = 'bytes'

        file_object = open(video_filename, 'rb')

        # if download is complete, output the file contents all at once
        # @todo is there a way to return as static file?
        #if (torrent_status.is_seeding):
        return file_object.read()

        # torrent_handle::file_progress   ?

        # switch to streaming mode
        cherrypy.response.stream = True

        # yields chunks of data or sleep until data is available
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

    print('httpd starting on port', settings['http_port'])

    print()
    access_url = 'http://' + settings['http_host']
    if settings['http_port'] != 80:
            access_url += ':' + str(settings['http_port'])
    access_url += '/'
    print('Point your browser to', access_url)
    print()


    cherrypy.quickstart(
        RootController(),
        '/',
        {
            '/': {
                #'tools.sessions.on': True,
                'tools.staticdir.on': True,
                #'tools.staticdir.root': ht_dir,
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
