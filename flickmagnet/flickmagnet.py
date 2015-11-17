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

def main():

    logging.basicConfig(
        filename = os.path.join(config.cache_dir, config.app_name + '.log'),
        level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s',
    )

    logging.info('Starting '+config.settings['server']['name']+' version '+config.settings['server']['version'])

    print('Starting '+config.settings['server']['name']+' '+config.settings['server']['version'])

    # start torrentd
    torrentd_pid = os.fork()
    if torrentd_pid == 0:
        #os._exit(0) # dont actually start
        torrentd.start(config.settings['server'], config.db_connect, config.cache_dir)

    # start httpd
    httpd_pid = os.fork()
    if httpd_pid == 0:
        #os._exit(0) # dont actually start
        httpd.start(config.settings['server'], config.db_connect)

    # start spiderd
    spiderd_pid = os.fork()
    if spiderd_pid == 0:
        #os._exit(0) # dont actually start
        spiderd.start(config.settings['server'], config.db_connect)

    while True:
        #print('main loop')
        time.sleep(60)

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

