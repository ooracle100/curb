import socket
import sys

_orig_getaddrinfo = socket.getaddrinfo

def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == 'api2.bybit.com':
        return _orig_getaddrinfo('23.32.248.27', port, family, type, proto, flags)
    if host == 'p2p.binance.com':
        return _orig_getaddrinfo('108.156.221.23', port, family, type, proto, flags)
    return _orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = patched_getaddrinfo

import sys
sys.path.insert(0, '/Users/orcl/Documents/curb')
from scripts import fetch_rates
fetch_rates.main()
