#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""

__created__ = '2018/03/09'
__author__ = 'killmoon'
"""

SOCKS_VERSION_5 = b'\x05'

METHOD_NO_AUTH = b'\x00'
METHOD_GSSAPI = b'\x01'
METHOD_USERPWD = b'\x02'
METHOD_IANA = b'\x03'
METHOD_PERSONAL = b'\x80'
METHOD_FAILURE = b'\xFF'

CMD_CONNECT = b'\x01'
CMD_BIND = b'\x02'
CMD_UDP = b'\x03'

RSV = b'\x00'

ATYP_IPV4 = b'\x01'
ATYP_HOSTNAME = b'\x03'
ATYP_IPV6 = b'\x04'


REP_SUCCESS = b'\x00'
REP_FAILURE = b'\x01'
REP_RULE_UNCONNECT = b'\x02'
REP_NET_NOT_ARRIVE = b'\x03'
REP_HOST_NOT_ARRIVE = b'\x04'
REP_CONNECT_REFUSE = b'\x05'
REP_TTL_TIMEOUT = b'\x06'
REP_UNAVAILABLE_CMD = b'\x07'
REP_UNAVAILABLE_ATYP = b'\x08'

