#!/usr/bin/env python3

import unittest
import config
import re

class TestConfig(unittest.TestCase):

  # version formatted like: 0.0.1
  def test_version(self):
    self.assertTrue(re.match(r'\d+\.\d+\.\d+', config.settings['server']['version']))

if __name__ == '__main__':
    unittest.main()
