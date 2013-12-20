import cgi
import cgitb
cgitb.enable()

from BaseHTTPServer import HTTPServer
from CGIHTTPServer import CGIHTTPRequestHandler
#from http.server import HTTPServer, CGIHTTPRequestHandler

host = "127.0.0.1"
port = 8080

httpd = HTTPServer((host, port), CGIHTTPRequestHandler)
print("Starting simple_httpd on port: " + str(httpd.server_port))
httpd.serve_forever()

