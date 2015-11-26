#!/usr/bin/env python3

import unittest

import spiderd

import requests

class TestSpiderd(unittest.TestCase):

    # connected to Internet?
    @unittest.skip("too slow")
    def test_internet(self):
        requests_session = requests.Session()
        self.assertTrue(spiderd.internet_works(requests_session))
        requests_session.close()

if __name__ == '__main__':
    unittest.main()
