from rest_framework.response import Response
from rest_framework.views import APIView
import os
import socket

# Create your views here.

SOCKFILE = '/tmp/hello_sock'

class HelloView(APIView):

    def get(self, format=None):
        # send event by using Unix Domain Socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        try:
            sock.connect(SOCKFILE)
            sock.sendall('{"Hello": "World"}')
        except Exception, ex:
            print ex
            print 'connect error'

        return Response({})

