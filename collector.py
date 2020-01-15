import threading
import time

# Number of seconds to wait between polling
POLL_TIMEOUT = 1

class Collector(threading.Thread):
    def __init__(self, log_fd, subscriber):
        super().__init__()
        self.log_fd = log_fd
        self.subscriber = subscriber

    def run(self):
        while True:
            # Read lines until 10Mb of logs have been read
            lines = self.log_fd.readlines(10 * 1024 * 1024)
            self.subscriber.feed(lines)
            time.sleep(POLL_TIMEOUT)
