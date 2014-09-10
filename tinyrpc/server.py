#!/usr/bin/python
# -*- coding: utf-8 -*-

from ryu.contrib.tinyrpc.transports.wsgi import WsgiServerTransport
from ryu.contrib.tinyrpc.server import RPCServer
from ryu.contrib.tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from ryu.contrib.tinyrpc.dispatch import RPCDispatcher

def hello():
    return 'Hello world'

def main():
    transport = WsgiServerTransport()
    protocol = JSONRPCProtocol()
    dispatcher = RPCDispatcher()
    dispatcher.add_method(hello)

    rpc_server = RPCServer(transport, protocol, dispatcher)
    rpc_server.serve_forever()



if __name__ == '__main__':
    main()
