#!/usr/bin/env python3

import unittest

import config
import torrentd

import os
import requests

class TestTorrentd(unittest.TestCase):

    # listen to the torrent port in a new process, then check that it works
    def test_port(self):

        # start torrentd in the background
        torrentd_pid = os.fork()
        if torrentd_pid == 0:
            torrentd.start(config.settings['server'], config.db_connect, config.cache_dir)

        # @todo actually test something
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
