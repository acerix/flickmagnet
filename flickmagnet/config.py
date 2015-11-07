
import os
import shutil
import pytoml as toml
import socket

app_name = 'flickmagnet'




# define filesystem paths

from xdg import BaseDirectory
package_dir = os.path.dirname(os.path.realpath(__file__))
config_dir = BaseDirectory.save_config_path(app_name)
data_dir = BaseDirectory.save_data_path(app_name)
cache_dir = BaseDirectory.save_cache_path(app_name)
#runtime_dir = BaseDirectory.get_runtime_dir(app_name)

config_file = os.path.join(config_dir, 'config.toml')


# load config file

if not os.path.isfile(config_file):
    shutil.copyfile(os.path.join(package_dir, 'examples/config.toml'), config_file)

with open(config_file) as config_file_object:
    settings = toml.load(config_file_object)


# where downloads are stored

settings['server']['download_dir'] = cache_dir


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
    s.connect(('flickmag.net',80))
    settings['server']['http_host'] = s.getsockname()[0]
    s.close()

    # sometimes gets the local network IP?
    #settings['server']['http_host'] = socket.gethostbyname(socket.getfqdn())



# test listener ports / get random ones

http_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
torrent_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# test http port or get a random one if not defined
if 'http_port' in settings['server']:
    http_sock.bind((settings['server']['http_addr'], settings['server']['http_port']))

else:
    http_sock.bind((settings['server']['http_addr'], 0))
    settings['server']['http_port'] = http_sock.getsockname()[1]

# test torrent port or get a random one if not defined
if 'torrent_port' in settings['server']:
    torrent_sock.bind(('0.0.0.0', settings['server']['http_port']))

else:
    torrent_sock.bind(('0.0.0.0', 0))
    settings['server']['torrent_port'] = torrent_sock.getsockname()[1]

# @todo would be better to keep open
http_sock.close()
torrent_sock.close()




# define database connection

import sqlite3

def db_connect():
    db = sqlite3.connect( os.path.join(data_dir, app_name + '.db') )
    db.row_factory = sqlite3.Row
    # @todo create database tables on first run
    return db



# cache the name:id of each table row in a hash table
def db_table_to_name_dict(table_name, key_column='name', value_column='id'):
    db = db_connect()
    result = {}
    for row in db.execute("""
SELECT
    `"""+key_column+"""` k,
    `"""+value_column+"""` v
FROM
    `"""+table_name+"""`
ORDER BY
    `"""+key_column+"""`
"""):
        result[row['k']] = row['v']

    return result

# cached tables
settings['server']['cached_tables'] = {}
settings['server']['cached_tables']['entity_type'] = db_table_to_name_dict('entity_type');
settings['server']['cached_tables']['magnet_file_status'] = db_table_to_name_dict('magnet_file_status');
settings['server']['cached_tables']['tag'] = db_table_to_name_dict('tag');

