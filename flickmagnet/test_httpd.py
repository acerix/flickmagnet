#!/usr/bin/env python3

import unittest

import config
import httpd

import os
import requests

class TestHttpd(unittest.TestCase):

    # listen to the http port in a new process, then check that robots.txt file matches
    def test_robots_txt(self):

        file_uri = 'robots.txt'

        # start httpd in the background
        httpd_pid = os.fork()
        if httpd_pid == 0:
            httpd.start(config.settings['server'], config.db_connect)

        response = requests.get('http://'+config.settings['server']['http_addr']+':'+str(config.settings['server']['http_port'])+'/'+file_uri)

        f = open(os.path.join(config.settings['server']['htdocs_dir'], file_uri),'r')
        expected_response = f.read()
        f.close()

        self.assertEqual(expected_response, response.text)

if __name__ == '__main__':
    unittest.main()
