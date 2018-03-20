#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""

__created__ = '2018/03/20'
__author__ = 'killmoon'
"""
import socks5.socks5_server as s5_server


if __name__ == '__main__':
    server = s5_server.start_server("0.0.0.0", 11030)
    s5_server.loop_forever(server)
