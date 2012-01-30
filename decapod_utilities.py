import os
import shutil
import subprocess

def makeDirs(path, mode=0777):
    if not os.path.exists(path):
        os.makedirs(path, mode)

def rmTree(path, ignore_errors=False, onerror=None):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors, onerror)
        
def writeToFile(contents, writePath, writeMode="w"):
    f = open(writePath, writeMode)
    f.write(contents)
    f.close()
    
def invokeCommandSync(cmdArgs, error, message):
    proc = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    if proc.returncode != 0:
        print(output)
        raise error, message
    
    return output
