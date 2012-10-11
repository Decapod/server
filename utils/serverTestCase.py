from cherrypy.test import helper
import os
import uuid
import mimetypes

class ServerTestCase(helper.CPWebCase):
    '''
    A subclass of helper.CPWebCase
    The purpose of this class is to add new common test functions that can be easily shared
    by various test classes.
    '''
    def assertUnsupportedHTTPMethods(self, url, methods):
        '''
        Tests that unsuppored http methods return a 405
        '''     
        for method in methods:
            self.getPage(url, method=method)
            self.assertStatus(405, "Should return a 405 'Method not Allowed' status for '{0}'".format(method))
            
    def fileUploadParams(self, path):
        '''
        Generates the headers and body needed to POST a file upload, for the file at 'path'
        '''
        CRLF = "\r\n"
        fileName = os.path.split(path)[1]
        fileType = mimetypes.guess_type(path)[0]
        id = uuid.uuid4()
        boundary = "---------------------------" + id.hex
        
        f = open(path)
        read = f.read()
        f.close()
        
        body = '--{0}{1}Content-Disposition: form-data; name="file"; filename="{2}"{1}Content-Type: {3}{1}{1}{4}{1}--{0}--{1}'.format(boundary, CRLF, fileName, fileType, read)
        headers = [
            ("Content-Length", len(body)),
            ("Content-Type", "multipart/form-data; boundary=" + boundary),
            ("Pragma", "no-cache"),
            ("Cache-Control", "no-cache")
        ]
        
        return headers, body
    
    def uploadFile(self, url, path, method="POST"):
        '''
        Posts the file at 'path' to the resource at 'url'
        '''
        headers, body = self.fileUploadParams(path)
        self.getPage(url, headers, method, body)