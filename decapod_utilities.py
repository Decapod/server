import os
import shutil
import subprocess

def makeDirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
    
def invokeCommandSync(cmdArgs, error, message):
    proc = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    if proc.returncode != 0:
        print(output)
        raise error, message
    
    return output