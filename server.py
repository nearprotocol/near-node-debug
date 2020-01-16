from pymongo import MongoClient
import utils
import threading
import time

# Number of seconds to wait between polling
POLL_TIMEOUT = 2

class Handler:
    def __init__(self, name, collection):
        self.name = name
        self.collection = collection

    def feed(self, lines):
        print(self.name, len(lines))
        to_insert = []

        for doc in utils.parse_all(lines):
            doc['_origin'] = self.name
            to_insert.append(doc)

        if to_insert:
            self.collection.insert_many(to_insert)


class DBAccess:
    def __init__(self, addr, name):
        ip, port = addr.split(':')
        client = MongoClient(ip, int(port))
        db = client[name]
        self.collection = db['data']


    def handler(self, name):
        return Handler(name, self.collection)


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
            if len(lines) < 10:
                time.sleep(POLL_TIMEOUT)
