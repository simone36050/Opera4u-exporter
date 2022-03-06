#!/usr/bin/python3.7

#import sys
#sys.path.insert(0, "~/.local/lib/python3.7/site-packages")
#: optional path to your local python site-packages folder
#import sys
#sys.path.insert(0, '<your_local_path>/lib/python<your_python_version>/site-packages')

from flup.server.fcgi import WSGIServer
from website import app

class ScriptNameStripper(object):
   def __init__(self, app):
       self.app = app

   def __call__(self, environ, start_response):
       environ['SCRIPT_NAME'] = ''
       return self.app(environ, start_response)

app = ScriptNameStripper(app)

if __name__ == '__main__':
    WSGIServer(app).run()