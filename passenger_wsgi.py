# import os
# import sys


# sys.path.insert(0, os.path.dirname(__file__))


# def application(environ, start_response):
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     message = 'It works!\n'
#     version = 'Python %s\n' % sys.version.split()[0]
#     response = '\n'.join([message, version])
#     return [response.encode()]

import sys, os 
cwd = os.getcwd() 
sys.path.append(cwd) 
sys.path.append(cwd) 
os.environ['DJANGO_SETTINGS_MODULE'] = "TechManager.settings" 
from django.core.wsgi import get_wsgi_application 
application = get_wsgi_application()