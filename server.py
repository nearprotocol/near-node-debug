from pymongo import MongoClient
import utils


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
            print(self.name, len(to_insert))
            self.collection.insert_many(to_insert)


class DBAccess:
    def __init__(self, addr, name):
        ip, port = addr.split(':')
        client = MongoClient(ip, int(port))
        db = client[name]
        self.collection = db['data']


    def handler(self, name):
        return Handler(name, self.collection)
