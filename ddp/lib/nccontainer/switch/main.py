#!/usr/bin/env python
import sys
import argparse
import logging

from nccontainer.common.logger import logger
from nccontainer.switch.switch_proxy import SwitchProxy
from nccontainer.switch.switch_proxy_new import SwitchProxy as SwitchProxy2


def parse_argument():
    parser = argparse.ArgumentParser(
        description='Network Consistency Container Tunnel Proxy')
    parser.add_argument('-b', '--bind', dest='bind', default='',
                        help='Bind IP address for the proxy (default: "").')
    parser.add_argument('-p', '--port', dest='port',
                        default='9090', type=int,
                        help='TCP port the proxy will listen on (default: 9090).')
    parser.add_argument('--forward', dest='forward',
                        default='localhost:6633',
                        help='IP:TCP_PORT, socket address the proxy will forward to (default: "localhost:6633").')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbosity to trace log.')
    return parser


def get_valid_forward(forward_str):
    forward = forward_str.split(':')
    assert len(forward) == 2
    addr = forward[0]
    port = int(forward[1])
    return addr, port


def main():
    parser = parse_argument()
    config = parser.parse_args(sys.argv[1:])
    if config.verbose:
        logger.setLevel(logging.DEBUG)
    forward_addr, forward_port = get_valid_forward(config.forward)
    # server = SwitchProxy(host=config.bind, port=config.port,
    #                      forward_addr=forward_addr, forward_port=forward_port)
    server = SwitchProxy2(config.bind, config.port,forward_addr, forward_port, config.bind, 12306)
    try:
        server.main_loop()
    except KeyboardInterrupt:
        print("Ctrl C - Stopping server")
        sys.exit(1)
    except Exception as e:
        print(str(e))
        import os
        os._exit(-1)


if __name__ == '__main__':
    main()
