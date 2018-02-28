#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""

__created__ = '2018/02/07'
__author__ = 'killmoon'
"""
import socket
import sys
import select
import struct
import logging
from socketserver import ThreadingTCPServer, StreamRequestHandler

logging.basicConfig(format='%(asctime)s %(message)s', filename='../.log/proxy.log', level=logging.INFO)


class Socks5Server(StreamRequestHandler):

    @staticmethod
    def handle_tcp(sock, remote):
        fdset = [sock, remote]
        while True:
            r, w, e = select.select(fdset, [], [])
            if sock in r:
                if remote.send(sock.recv(4096)) <= 0:
                    break
            if remote in r:
                if sock.send(remote.recv(4096)) <= 0:
                    break

    def handle(self):
        try:
            logging.info('socks connection from IP:{},Port:{}'.format(self.client_address[0],self.client_address[1]))
            sock = self.connection
            # 1. Version
            content = sock.recv(256)
            logging.info(content)
            sock.send(b"\x05\x00")
            # 2. Request
            data = self.rfile.read(4).decode()
            mode = ord(data[1])
            addrtype = ord(data[3])
            if addrtype == 1:  # IPv4
                addr = socket.inet_ntoa(self.rfile.read(4))
            elif addrtype == 3:  # Domain name
                addr = self.rfile.read(ord(sock.recv(1)[0].decode()))
            port = struct.unpack('>H', self.rfile.read(2))
            reply = b"\x05\x00\x00\x01"
            try:
                if mode == 1:  # 1. Tcp connect
                    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote.connect((addr, port[0]))
                    logging.info(' Tcp connect to {}, {}'.format(addr, port[0]))
                else:
                    reply = b"\x05\x07\x00\x01"  # Command not supported
                local = remote.getsockname()
                reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
            except socket.error:
                # Connection refused
                reply = b'\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00'
            sock.send(reply)
            # 3. Transfering
            if reply[1] == b'\x00':  # Success
                if mode == 1:  # 1. Tcp connect
                    self.handle_tcp(sock, remote)
        except socket.error:
            logging.warning('SOCKET ERROR')


def proxy_socket(port):
    logging.info('New socks5 server is started !')
    logging.info('Socks5 proxy server port is:{}'.format(port))
    server = ThreadingTCPServer(('0.0.0.0', int(port)), Socks5Server)
    server.serve_forever()


if __name__ == '__main__':
    try:
        assert int(sys.argv[1])
        assert 1000 < int(sys.argv[1]) < 65534
        proxy_socket(sys.argv[1])
    except (IndexError, AssertionError):
        proxy_socket(1018)
