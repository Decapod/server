import sys
import os
import unittest

sys.path.append(os.path.abspath('..'))
import resourcesource

class ResourceSourceTest(unittest.TestCase):
    resourceSource = None
    
    def setUp(self):
        self.resourceSource = resourcesource.ResourceSource("data/resource-source-test-data.json")

        
    def test_loadConfig(self):
        self.assertEquals(1, len(self.resourceSource.resources))
    
    def test_filePath(self):
        jsPath = self.resourceSource.filePath("js")
        self.assertEquals(jsPath, \
                          resourcesource.serverBasePath \
                          + "../decapod-ui/components/capture/js")
        
        # Test an invalid resource name
        invalidPath = self.resourceSource.filePath("invalid")
        self.assertEquals(invalidPath, None)
        
    def test_webURL(self):
        jsURL = self.resourceSource.webURL("js")
        self.assertEquals(jsURL, "/js")
        
        # Test an invalid resource name
        invalidURL = self.resourceSource.webURL("invalid")
        self.assertEquals(invalidURL, None)
        
    def test_cherryPyConfig(self):
        config = self.resourceSource.cherryPyConfig()
        self.assertEquals(2, len(config))
        root = config["/"]
        self.assertEqual(root, {
            "tools.staticdir.root": resourcesource.serverBasePath                        
        })
        js = config["/js"]
        self.assertEqual(js, {
            "tools.staticdir.on": True,
            "tools.staticdir.dir": "../decapod-ui/components/capture/js"
        })
        
        
if __name__ == "__main__":
    unittest.main()
    