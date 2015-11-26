#!/usr/bin/env python3

import unittest

import config

import re

class TestConfig(unittest.TestCase):

    # version formatted like: 0.0.1
    def test_version(self):
        self.assertTrue(re.match(r'\d+\.\d+\.\d+', config.settings['server']['version']))

    # db tables loaded to cache
    def test_cached_tables(self):
        self.assertEqual(3, len(config.settings['server']['cached_tables']['entity_type']))
        self.assertEqual(4, len(config.settings['server']['cached_tables']['entity_status']))
        self.assertEqual(8, len(config.settings['server']['cached_tables']['magnet_file_status']))
        self.assertEqual(22, len(config.settings['server']['cached_tables']['tag']))

if __name__ == '__main__':
    unittest.main()
