
import random
import threading
import time
from collections import deque
from wsgiref.simple_server import make_server

from prometheus_client import (Counter, Gauge, Histogram, Summary,
                               make_wsgi_app, start_http_server)

import core


class GaugeWithDelta:
    def __init__(self, name, doc, interval):
        self.main = Gauge(f"{name}", f"{doc}")
        self.delta = Gauge(
            f"{name}_delta", f"Delta from the last {interval} seconds from {doc}")
        self.deq_size = Gauge(
            f"{name}_deq_size", f"Size of the deque internally from {doc}")
        self.deq = deque()
        self.interval = interval

    def add(self, value):
        self.main.set(value)
        now = time.time()
        self.deq.append((now, value))
        while now - self.deq[0][0] > self.interval:
            self.deq.popleft()
        if self.deq[0][1] == self.deq[-1][1]:
            g_per_interval = 1. / self.interval
        else:
            g_per_interval = (self.deq[-1][1] -
                              self.deq[0][1] - 1) / (self.deq[-1][0] - self.deq[0][0])
        self.delta.set(g_per_interval)
        self.deq_size.set(len(self.deq))


handle_calls = Counter("handle_message_calls",
                       "All calls to handle message so far.")

highest_block = GaugeWithDelta("highest_block", "Latest block", 60)

validators = Gauge("validators", "Validators")

all_messages = {}


def handle_message(api, node):
    handle_calls.inc()
    # Record heights
    heights = api.heights()
    highest_block.add(max(heights))

    stats = api.stats_per_type_of_message()

    validators.set(api.validators())
    for key, stat in stats.items():
        if not key in all_messages:
            all_messages[key] = [GaugeWithDelta(
                f"{key}_{name}", f"{doc} {key}", 60) for (name, doc) in
                [("count_sum", "Count sum of"),
                 ("count_max", "Count max of"),
                 ("bytes_sum", "Bytes sum of"),
                 ("bytes_max", "Bytes max of")]
            ]

        for val, g in zip(stat, all_messages[key]):
            g.add(val)


if __name__ == '__main__':
    api = core.Api('http://localhost:3030', handle_message)

    app = make_wsgi_app()
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
