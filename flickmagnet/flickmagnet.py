#!/usr/bin/env python3

# config
import config

# sub processes
import httpd
import torrentd
import spiderd

import logging
import sys
import os
import time

from multiprocessing import Process

def main():

    logging.basicConfig(
        filename = os.path.join(config.cache_dir, config.app_name + '.log'),
        level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s',
    )

    logging.info('Starting '+config.settings['server']['name']+' version '+config.settings['server']['version'])

    print('Starting '+config.settings['server']['name']+' '+config.settings['server']['version'])

    # start torrentd
    torrentd_process = Process(target=torrentd.start, args=(config.settings['server'], config.db_connect, config.cache_dir))
    torrentd_process.start()

    # start httpd
    httpd_process = Process(target=httpd.start, args=(config.settings['server'], config.db_connect))
    httpd_process.start()

    # start spiderd
    spiderd_process = Process(target=spiderd.start, args=(config.settings['server'], config.db_connect))
    spiderd_process.start()

    print()
    access_url = 'http://' + config.settings['server']['http_host']
    if config.settings['server']['http_port'] != 80:
            access_url += ':' + str(config.settings['server']['http_port'])
    access_url += '/'
    print('Listening on', access_url)
    print()

    while True:
        #print('main loop')
        time.sleep(60)


# the if fixes windows bs
if __name__ == "__main__":
    main()

import daemonocle

def cb_shutdown(message, code):
    logging.info('Daemon is stopping')
    logging.debug(message)

if __name__ == '__main__':
    daemon = daemonocle.Daemon(
        worker=main,
        shutdown_callback=cb_shutdown,
        pidfile = os.path.join(config.runtime_dir, config.app_name + '.pid'),
    )
    if (len(sys.argv) > 1):
        daemon.do_action(sys.argv[1])

