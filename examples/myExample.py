#!/usr/bin/env python

"""
Demo a custom implementation of the bdpPvaMetadata Example.

Add minimal effort in each part to be customized.  Just for demo.
"""

import time
import bdpPvaMetadata

DEFAULT_CHANNEL = "Bdp1:Handshake"

class MyServer(bdpPvaMetadata.Server):
    def getValue(self):
        return {"example": 1.0}

class MyListener(bdpPvaMetadata.Listener):
    def monitor(self, pv_object):
        print(self.getValue(pv_object))

def run_server(duration=10, period=1):
    channel = DEFAULT_CHANNEL

    server = MyServer(channel)
    deadline = time.time() + duration
    while time.time() < deadline:
        server.publishContent(server.getValue())
        time.sleep(period)
    server.stop()

if __name__ == "__main__":
    run_server()
