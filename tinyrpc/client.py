#!/usr/bin/python
# -*- coding: utf-8 -*-

from ryu.contrib.tinyrpc.client import RPCClient
from ryu.contrib.tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from ryu.contrib.tinyrpc.transports.http import HttpPostClientTransport

def main():
    protocol = JSONRPCProtocol()
    transport = HttpPostClientTransport('127.0.0.1')
    rpc_client = RPCClient(protocol, transport)

    print rpc_client.call('hello', None, None)


if __name__ == '__main__':
    main()
