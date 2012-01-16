import sys
import os
import unittest
import testutils
sys.path.append(os.path.abspath('..'))
import resourcesource

JS_PATH_ROOT = resourcesource.serverBasePath + "/" + "components/mock/js"

class ResourceSourceTest(unittest.TestCase):
    resourceSource = None
    
    def setUp(self):
        self.resourceSource = testutils.createTestResourceSource()
    
    def test_parsePathHead(self):
        head = resourcesource.parsePathHead("${js}/foo/bar.jpg")
        self.assertEquals("${js}/foo/", head)
        
    def test_loadConfig(self):
        self.assertEquals(5, len(self.resourceSource.resources))
    
    def test_filePathForResource(self):
        jsPath = self.resourceSource.filePathForResource("js")
        self.assertEquals(jsPath, JS_PATH_ROOT)
        
        # Test an invalid resource name
        invalidPath = self.resourceSource.filePathForResource("invalid")
        self.assertEquals(invalidPath, None)
        
    def test_parseFileName(self):
        name = resourcesource.parseFileName("${js}/foo/bar.jpg")
        self.assertEquals(2, len(name))
        self.assertEquals("bar", name[0])
        self.assertEquals("jpg", name[1])
        
    def test_filePath(self):
        # Test just the resource token
        path = self.resourceSource.filePath("${js}")
        self.assertEquals(path, JS_PATH_ROOT)
        
        # Test the resource token with additional path segments
        path = self.resourceSource.filePath("${js}/cat/dog")
        self.assertEquals(path, JS_PATH_ROOT + "/cat/dog")
        
        # Test with a file at the end of the path 
        path = self.resourceSource.filePath("${js}/cat/dog/hamster.js")
        self.assertEquals(path, JS_PATH_ROOT + "/cat/dog/hamster.js")

        # Test with no resource token
        invalidURL = self.resourceSource.filePath("invalid")
        self.assertEquals(invalidURL, None)
              
        # Test with an invalid token name
        invalidURL = self.resourceSource.filePath("${invalid}/cat/dog")
        self.assertEquals(invalidURL, None)
        
    def test_virtualPath(self):
        absolutePath = JS_PATH_ROOT + "/cat/dog"
        result = self.resourceSource.virtualPath(absolutePath)
        self.assertEquals(result, "${js}/cat/dog")
        
        absolutePath = "/invalid/path/cat/dog"
        result = self.resourceSource.virtualPath(absolutePath)
        self.assertEquals(result, absolutePath)
        
    def test_webURLForResource(self):
        jsURL = self.resourceSource.webURLForResource("js")
        self.assertEquals(jsURL, "/js")
        
        # Test an invalid resource name
        invalidURL = self.resourceSource.webURLForResource("invalid")
        self.assertEquals(invalidURL, None)
        
    def test_webURL(self):
        # Test just the resource token
        url = self.resourceSource.webURL("${js}")
        self.assertEquals(url, "/js")
        
        # Test the resource token with additional path segments
        url = self.resourceSource.webURL("${js}/cat/dog")
        self.assertEquals(url, "/js/cat/dog")
        
        # Test with no resource token
        invalidURL = self.resourceSource.webURL("invalid")
        self.assertEquals(invalidURL, None)
              
        # Test with an invalid token name
        invalidURL = self.resourceSource.webURL("${invalid}/cat/dog")
        self.assertEquals(invalidURL, None)

    def test_cherryPyConfig(self):
        config = self.resourceSource.cherryPyConfig()
        self.assertEquals(6, len(config))
        root = config["/"]
        self.assertEqual(root, {
            "tools.staticdir.root": resourcesource.serverBasePath                        
        })
        js = config["/js"]
        self.assertEqual(js, {
            "tools.staticdir.on": True,
            "tools.staticdir.dir": "components/mock/js"
        })
        
        
if __name__ == "__main__":
    unittest.main()
    