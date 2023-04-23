#!/usr/bin/env python

"""
Demo a custom server using the bdpPvaMetadata Example.

Add minimal effort in each part to be customized.  Just for demo.
"""

import time
import bdp_handshake

DEFAULT_CHANNEL = "Bdp1:Handshake"


class MyServer(bdp_handshake.HandshakeServer):
    def getDictionary(self):
        return {"example": 1.0}


def run_server(duration=10, period=1):
    channel = DEFAULT_CHANNEL

    server = MyServer(channel)
    server.start()
    deadline = time.time() + duration
    while time.time() < deadline:
        server.publishDictionary(server.getDictionary())
        time.sleep(period)
    server.stop()


if __name__ == "__main__":
    run_server()
