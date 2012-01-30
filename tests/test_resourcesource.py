import sys
import os
import unittest
sys.path.append(os.path.abspath('..'))
import resourcesource as rs


CONFIG_FILE = os.path.abspath("data/config/decapod-test.conf")
LIBRARY_PATH = "data/library"
MOCK_CONFIG = {"/library": {"tools.staticdir.dir": LIBRARY_PATH}}
    
class TestResourceSource(unittest.TestCase):
    
    def test_01_parseVirtualPath_validNoPath(self):
        token, path = rs.parseVirtualPath("${library}")
        self.assertEquals("/library", token)
        self.assertEquals("", path)
        
    def test_02_parseVirtualPath_validWithPath(self):
        token, path = rs.parseVirtualPath("${library}/path")
        self.assertEquals("/library", token)
        self.assertEquals("path", path)
        
    def test_03_parseVirtualPath_invalid(self):
        self.assertRaises(Exception, rs.parseVirtualPath, "library")
        self.assertRaises(Exception, rs.parseVirtualPath, "$library")
        self.assertRaises(Exception, rs.parseVirtualPath, "$library}")
        self.assertRaises(Exception, rs.parseVirtualPath, "${library")
        self.assertRaises(Exception, rs.parseVirtualPath, "{library")
        self.assertRaises(Exception, rs.parseVirtualPath, "{library}")
        self.assertRaises(Exception, rs.parseVirtualPath, "library}")
        
    def tests_04_url(self):
        url = rs.url("${library}/path")
        self.assertEquals("http://127.0.0.1:8080/library/path", url)
        
    def tests_05_url_invalidVirtualPath(self):
        self.assertRaises(Exception, rs.url, "library/path")
        
    def tests_06_path_absolute(self):
        path = rs.path("${library}/path", config=MOCK_CONFIG)
        self.assertEqual(os.path.abspath(os.path.join(LIBRARY_PATH, "path")), path)
        
    def tests_07_path_relative(self):
        path = rs.path("${library}/path", False,MOCK_CONFIG)
        self.assertEqual(os.path.join(LIBRARY_PATH, "path"), path)
        
if __name__ == '__main__':
    unittest.main()
