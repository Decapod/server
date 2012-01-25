import sys
import os
import unittest
import testutils
sys.path.append(os.path.abspath('..'))
import resourcesource
import cherrypy

JS_PATH_ROOT = resourcesource.serverBasePath + "/" + "components/mock/js"

class ResourceSourceTest(unittest.TestCase):
    resourceSource = None
    
    def setUp(self):
        self.resourceSource = testutils.createTestResourceSource()
    
    def test_01_parsePathHead(self):
        head = resourcesource.parsePathHead("${js}/foo/bar.jpg")
        self.assertEquals("${js}/foo/", head)
        
    def test_02_parseFileName(self):
        name = resourcesource.parseFileName("${js}/foo/bar.jpg")
        self.assertEquals(2, len(name))
        self.assertEquals("bar", name[0])
        self.assertEquals("jpg", name[1])
        
    def test_03_appendSuffix(self):
        expectedPath = "${js}/foo/bar-test.jpg"
        actualPath = resourcesource.appendSuffix("${js}/foo/bar.jpg", "-test")
        self.assertEquals(expectedPath, actualPath)
        
    def test_04_loadConfig(self):
        self.assertEquals(5, len(self.resourceSource.resources))
    
    def test_05_filePathForResource_valid(self):
        jsPath = self.resourceSource.filePathForResource("js")
        self.assertEquals(jsPath, JS_PATH_ROOT)
        
    def test_06_filePathForResources_invalid(self):
        # Test an invalid resource name
        invalidPath = self.resourceSource.filePathForResource("invalid")
        self.assertEquals(invalidPath, None)
        
    def test_07_filePath_noToken(self):
        invalidURL = self.resourceSource.filePath("invalid")
        self.assertEquals(invalidURL, None)
        
    def test_08_filePath_invalidToken(self):
        invalidURL = self.resourceSource.filePath("invalid")
        self.assertEquals(invalidURL, None)
        
    def test_09_filePath_validToken(self):
        path = self.resourceSource.filePath("${js}")
        self.assertEquals(path, JS_PATH_ROOT)
        
    def test_10_filePath_segments(self):
        path = self.resourceSource.filePath("${js}/cat/dog")
        self.assertEquals(path, JS_PATH_ROOT + "/cat/dog")
        
    def test_11_filePath_file(self):
        path = self.resourceSource.filePath("${js}/cat/dog/hamster.js")
        self.assertEquals(path, JS_PATH_ROOT + "/cat/dog/hamster.js")
    
    def test_12_virtualPath_valid(self):
        absolutePath = JS_PATH_ROOT + "/cat/dog"
        result = self.resourceSource.virtualPath(absolutePath)
        self.assertEquals(result, "${js}/cat/dog")
                          
    def test_13_virtualPath_invalid(self):
        absolutePath = "/invalid/path/cat/dog"
        result = self.resourceSource.virtualPath(absolutePath)
        self.assertEquals(result, absolutePath)
    
    def test_14_parseVirtualPath_none(self):
        absolutePath = None
        resourceName, pathSegs = self.resourceSource.parseVirtualPath(absolutePath)
        self.assertEquals(None, resourceName)
        self.assertEquals(None, pathSegs)
        
    def test_15_parseVirtualPath_invalid(self):
        absolutePath = "invalid/cat/dog"
        resourceName, pathSegs = self.resourceSource.parseVirtualPath(absolutePath)
        self.assertEquals(None, resourceName)
        self.assertEquals(None, pathSegs)
        
    def test_16_parseVirtualPath_valid(self):
        absolutePath = "${js}/cat/dog"
        resourceName, pathSegs = self.resourceSource.parseVirtualPath(absolutePath)
        self.assertEquals("js", resourceName)
        self.assertEquals(["cat", "dog"], pathSegs)
        
    def test_17_webURLForResource_valid(self):
        jsURL = self.resourceSource.webURLForResource("js")
        self.assertEquals(jsURL, "/js")
        
    def test_18_webURLForResource_invalid(self):
        invalidURL = self.resourceSource.webURLForResource("invalid")
        self.assertEquals(invalidURL, None)
    
    def test_19_weburl_noToken(self):
        invalidURL = self.resourceSource.webURL("invalid")
        self.assertEquals(invalidURL, None)
        
    def test_20_weburl_invalidToken(self):
        invalidURL = self.resourceSource.webURL("${invalid}/cat/dog")
        self.assertEquals(invalidURL, None)
    
    def test_21_weburl_token(self):
        url = self.resourceSource.webURL("${js}")
        self.assertEquals(url, "/js")
        
    def test_22_weburl_segments(self):
        url = self.resourceSource.webURL("${js}/cat/dog")
        self.assertEquals(url, "/js/cat/dog")

    def test_23_cherryPyConfig(self):
        config = self.resourceSource.cherryPyConfig()
        self.assertEquals(6, len(config))
        
        root = config["/"]
        self.assertEqual(root["tools.staticdir.root"], resourcesource.serverBasePath)
        self.assertTrue(isinstance(root["request.dispatch"], cherrypy.dispatch.MethodDispatcher))
        
        js = config["/js"]
        self.assertEqual(js, {
            "tools.staticdir.on": True,
            "tools.staticdir.dir": "components/mock/js"
        })
        
        
if __name__ == "__main__":
    unittest.main()
    