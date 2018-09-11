#!/usr/bin/env python3

import sys
import time
import pycurl

global g_downloaded
global g_uploaded
global timestamp
global graceful_period

def progress(tbd, downloaded, tbu, uploaded):
    global g_downloaded, g_uploaded, timestamp
    now = time.clock() * 1000000
    interval = now - timestamp

    if interval < graceful_period:
        return 0

    timestamp = now

    speed_d = (downloaded - g_downloaded) / interval
    speed_u = (uploaded - g_uploaded) / interval

    g_downloaded = downloaded
    g_uploaded = uploaded

    print("{} {:.2f} {:.2f} {} {}".format(int(now), speed_d, speed_u, downloaded, uploaded), file=sys.stderr)
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: {} TARGET_URL GRACEFUL_PERIOD".format(__file__))
        sys.exit(1)

    g_downloaded = 0
    g_uploaded = 0
    timestamp = time.clock() * 1000000
    graceful_period = int(sys.argv[2])

    task = pycurl.Curl()
    task.setopt(pycurl.URL, sys.argv[1])
    task.setopt(pycurl.NOPROGRESS, False)
    task.setopt(pycurl.XFERINFOFUNCTION, progress)
    task.perform()
