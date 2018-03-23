#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""

__created__ = '2018/03/09'
__author__ = 'killmoon'
"""
import logging
import platform
import struct
from socket import *
from selectors import *
import select
import threading
import socks as socks5

# 根据系统判断日志存储的路径 windows 存储在上级目录的.log中
# Linux等系统存储在log中统一管理
if platform.system() == 'Windows':
    filename = '../.log/socks5.log'
else:
    filename = '/killmoon/log/socks5.log'

# 格式化日志的格式
FORMAT = '[%(asctime)s] [%(levelname)s] [%(thread)d] %(message)s'
logging.basicConfig(filename=filename, level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# 发送所有数据
def send_all(sock, data):
    """
    发送数据
    :param sock: 发送数据的目标地址连接对象
    :param data: 发送的数据
    """
    bytes_sent = 0
    while True:
        r = sock.send(data[bytes_sent:])
        if r < 0:
            return r
        bytes_sent += r

        if bytes_sent == len(data):
            return bytes_sent


def handle_tcp(client, remote, client_ip, remote_ip):
    """
    客户端与目标地址的数据传输
    :param client: client对象
    :param remote: remote对象
    :param client_ip: 客户端IPV4地址
    :param remote_ip: 目标IPV4地址
    :return:
    """
    logger.info("Sending data between %s and %s !!!" % (client_ip, remote_ip))

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
                    logger.error("Failed pipping all data to %s !!!" % remote_ip)
                    break
            if remote in r:
                remote_data = remote.recv(1024 * 100)
                if len(remote_data) <= 0:
                    break
                result = send_all(client, remote_data)
                if result < len(remote_data):
                    logger.error("Failed pipping all data to %s !!!" % client_ip)
                    break
    finally:
        client.close()
        remote.close()
    logger.info("Piping data between %s and %s are done!" % (client_ip, remote_ip))


def handle_client_connect(conn):
    """
    处理连接请求
    :param conn:
    :return:
    """
    client, client_addr = conn.accept()
    logger.info("Client connected with IP: %s", client_addr)
    # 获取socks版本 methods的长度 METHODS是客户端支持的认证方式列表
    ver, methods = client.recv(1), client.recv(1)
    # 根据methods的长度获取methods
    methods = client.recv(ord(methods))
    # 发送给客户端当前服务端版本和支持的验证类型
    client.send(socks5.SOCKS_VERSION_5 + socks5.METHOD_NO_AUTH)
    # 服务端接收socks版本 cmd命令码 ip类型
    ver, cmd, rsv, atype = client.recv(1), client.recv(1), client.recv(1), client.recv(1)

    # 如果cmd不是connect请求
    if ord(cmd) is not 1:
        client.close()
        return
    # 如果地址类型是IPV4
    if ord(atype) == 1:
        remote_addr = inet_ntoa(client.recv(4))
        remote_port = struct.unpack(">H", client.recv(2))[0]
    # 如果地址类型是域名
    elif ord(atype) == 3:
        addr_len = ord(client.recv(1))
        remote_addr = client.recv(addr_len)
        remote_port = struct.unpack(">H", client.recv(2))[0]
    # 其他情况拒绝连接
    else:
        reply = socks5.SOCKS_VERSION_5 + socks5.REP_UNAVAILABLE_ATYP + socks5.RSV + socks5.ATYP_IPV4 + inet_aton(
            "0.0.0.0") + struct.pack(">H", 2222)
        logger.info("IP version is not IPV4, refused connect......")
        client.send(reply)
        client.close()
        return

    remote = socket(AF_INET, SOCK_STREAM)
    try:
        remote.connect((remote_addr, remote_port))
    except TimeoutError:
        logger.error("Connect time out with remote addr : %s " % remote_addr)

    logger.info("Connect to remote addr : %s:%s".format(remote_addr, remote_port))

    # 请求成功 继续发送数据
    reply = socks5.SOCKS_VERSION_5 + socks5.REP_SUCCESS + socks5.RSV + socks5.ATYP_IPV4 + inet_aton(
        "0.0.0.0") + struct.pack(">H", 2222)
    client.send(reply)
    # 在客户端和服务端之间传输数据
    handle_tcp(client, remote, client_addr, remote_addr)


def start_server(ip_addr: str, ip_port: int):
    """

    :param ip_addr:绑定的IP地址
    :param ip_port:绑定的IP端口
    :return: 返回server对象
    """
    server = socket(AF_INET, SOCK_STREAM)
    server.bind((ip_addr, ip_port))
    server.listen(1000)

    logger.info("Socks5 server listening on server: %s : %d ......" % (ip_addr, ip_port))
    return server


def thread_socks_connect(conn):
    """
    开启新线程处理连接
    :param conn: 一个连接
    :return:
    """
    t = threading.Thread(target=handle_client_connect, args=(conn,))
    t.start()
    logger.info("Socks start a new session!")


def loop_forever(server):
    """
    IO多路复用
    :param server: 正在监听的服务
    :return:
    """
    selector = DefaultSelector()
    selector.register(server, EVENT_READ, thread_socks_connect)
    while True:
        ready = selector.select()
        for key, event in ready:
            callback = key.data
            callback(key.fileobj)


if __name__ == '__main__':
    started_server = start_server('0.0.0.0', 10030)
    loop_forever(started_server)
