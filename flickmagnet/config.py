
import os
import math
import shutil
import toml
import socket

import ctypes
import platform
import sys

app_name = 'flickmagnet'


# define filesystem paths

from xdg import BaseDirectory
package_dir = os.path.dirname(os.path.realpath(__file__))
config_dir = BaseDirectory.save_config_path(app_name)
data_dir = BaseDirectory.save_data_path(app_name)
cache_dir = BaseDirectory.save_cache_path(app_name)
#runtime_dir = BaseDirectory.get_runtime_dir(app_name) # XDG_RUNTIME_DIR undefined in systemd?
runtime_dir = cache_dir

config_file = os.path.join(config_dir, 'config.toml')


# load config file
if not os.path.isfile(config_file):
    shutil.copyfile(os.path.join(package_dir, 'examples', 'config.toml'), config_file)

with open(config_file) as config_file_object:
    settings = toml.load(config_file_object)


# copy version number to settings
from version import __version__
settings['server']['version'] = __version__


# where downloads are stored
settings['server']['download_dir'] = cache_dir

# where pid file is stored
settings['server']['runtime_dir'] = runtime_dir

# where htdocs are stored
settings['server']['htdocs_dir'] = os.path.join(package_dir, 'htdocs')


# get a host name if not defined
if 'http_host' not in settings['server']:

    # usually resolves to 127.0.0.1 from hosts file
    #settings['server']['http_host'] = socket.gethostbyname(socket.gethostname())

    # only works for a fqdn
    #settings['server']['http_host'] = socket.getfqdn()

    # gets the local network IP, others on the network can connect to this
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('www.google.com',80))
    settings['server']['http_host'] = s.getsockname()[0]
    s.close()

    # sometimes gets the local network IP?
    #settings['server']['http_host'] = socket.gethostbyname(socket.getfqdn())



# test listener ports / get random ones

http_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
torrent_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# test http port or get a random one if not defined
if 'http_port' in settings['server']:
    pass
    #http_sock.bind((settings['server']['http_addr'], settings['server']['http_port']))

else:
    http_sock.bind((settings['server']['http_addr'], 0))
    settings['server']['http_port'] = http_sock.getsockname()[1]

# test torrent port or get a random one if not defined
if 'torrent_port' in settings['server']:
    torrent_sock.bind(('0.0.0.0', settings['server']['http_port']))

else:
    torrent_sock.bind(('0.0.0.0', 0))
    settings['server']['torrent_port'] = torrent_sock.getsockname()[1]

# @todo should keep these open
http_sock.close()
torrent_sock.close()



def get_free_space(dirname):
  """Return folder/drive free space in bytes"""
  if 'Windows'==platform.system():
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes))
    return free_bytes.value
  else:
    st = os.statvfs(dirname)
    return st.f_bavail * st.f_frsize


# default number of days to keep videos is number of free gigabytes in download dir, rounded up
if 'video_cache_days' not in settings['server']:
  settings['server']['video_cache_days'] = math.ceil(get_free_space(settings['server']['download_dir']) / 1073741824)


# database just initialized?
settings['server']['first_run'] = False


# define database connection
import sqlite3

def db_connect():
  db = sqlite3.connect( os.path.join(data_dir, app_name + '.db') )
  db.row_factory = sqlite3.Row
  return db


# test db connection
db = db_connect()

# initialize tables if none exist
table_count = db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]

if table_count is 0:
  settings['server']['first_run'] = True
  print('Initializing database...')

  # download media-torrent-db schema
  import urllib.request
  with urllib.request.urlopen('https://raw.githubusercontent.com/acerix/media-torrent-db/master/schema.sql') as f:
    schema_sql = f.read().decode('utf-8')

  # add to the database
  db.executescript(schema_sql)
