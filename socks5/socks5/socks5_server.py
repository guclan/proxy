#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""

__created__ = '2018/03/09'
__author__ = 'killmoon'
"""
import struct
from socket import *
from selectors import *
import select
import threading
import socks5.socks as SOCKS


def send_all(sock, data):
    bytes_sent = 0
    while True:
        r = sock.send(data[bytes_sent:])
        if r < 0:
            return r
        bytes_sent += r

        if bytes_sent == len(data):
            return bytes_sent


def handle_tcp(client, remote):
    print("piping data...")

    try:
        fds = [client, remote]
        while True:
            r, w, e = select.select(fds, [], [])
            if client in r:
                cli_data = client.recv(1024 * 100)
                if len(cli_data) <= 0:
                    break
                result = send_all(remote, cli_data)
                if result < len(cli_data):
                    print("Failed pipping all data to target!!!")
                    break
            if remote in r:
                remote_data = remote.recv(1024 * 100)
                if len(remote_data) <= 0:
                    break
                result = send_all(client, remote_data)
                if result < len(remote_data):
                    print("Failed pipping all data to client!!!")
                    break
    finally:
        client.close()
        remote.close()
    print("piping data done.")


def handle_client_connect(conn):
    client, addr = conn.accept()
    print("client connect:", addr)

    ver, methods = client.recv(1), client.recv(1)
    methods = client.recv(ord(methods))

    client.send(SOCKS.SOCKS_VERSION_5 + SOCKS.METHOD_NO_AUTH)

    ver, cmd, rsv, atype = client.recv(1), client.recv(1), client.recv(1), client.recv(1)

    if ord(cmd) is not 1:
        client.close()
        return

    if ord(atype) == 1:
        remote_addr = inet_ntoa(client.recv(4))
        remote_port = struct.unpack(">H", client.recv(2))[0]

    elif ord(atype) == 3:
        addr_len = ord(client.recv(1))
        remote_addr = client.recv(addr_len)
        remote_port = struct.unpack(">H", client.recv(2))[0]

    else:
        reply = SOCKS.SOCKS_VERSION_5 + SOCKS.REP_UNAVAILABLE_ATYP + SOCKS.RSV + SOCKS.ATYP_IPV4 + inet_aton(
            "0.0.0.0") + struct.pack(">H", 2222)
        client.send(reply)
        client.close()
        return
    print("cmd:{0} target ---> {1}:{2}".format(cmd, remote_addr, remote_port))

    remote = socket(AF_INET, SOCK_STREAM)
    remote.connect((remote_addr, remote_port))

    reply = SOCKS.SOCKS_VERSION_5 + SOCKS.REP_UNAVAILABLE_ATYP + SOCKS.RSV + SOCKS.ATYP_IPV4 + inet_aton("0.0.0.0") + struct.pack(">H", 2222)
    client.send(reply)
    handle_tcp(client, remote)


def start_server(ip_addr:str, ip_port:int):
    server = socket(AF_INET, SOCK_STREAM)
    server.bind((ip_addr, ip_port))
    server.listen(1000)

    print("server listening on port: %d" % ip_port)
    return server


def thread_socks_connect(conn):
    t = threading.Thread(target=handle_client_connect, args=(conn, ))
    t.start()


def loop_forever(started_server):
    selector = DefaultSelector()
    selector.register(started_server, EVENT_READ, thread_socks_connect)
    while True:
        ready = selector.select()
        for key, event in ready:
            callback = key.data
            callback(key.fileobj)


if __name__ == '__main__':
    server = start_server("0.0.0.0", 11030)
    loop_forever(server)
