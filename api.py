class Api:
    def __init__(self, db):
        self.collection = db.collection

    @property
    def total_entries(self):
        """
        Number of logs stored in the database.
        """
        return self.collection.count({})

    @property
    def logs_origin(self):
        """
        All path to logs from which logs were scraped.
        """
        return self.collection.distinct("_origin",  {})

    @property
    def keys(self):
        """
        All type of diagnostics currently stored
        """
        return self.collection.distinct("key", {})

    @property
    def direct_message_keys(self):
        """
        All type of direct message keys currently stored.
        `Routed` is one of them.

        [Expensive]
        """
        return next(self.collection.aggregate([
            {
                "$project": {
                "arrayofkeyvalue": {
                    "$objectToArray": "$msg"
                }
                }
            },
            {
                "$unwind": "$arrayofkeyvalue"
            },
            {
                "$group": {
                "_id": "null",
                "keys": {
                    "$addToSet": "$arrayofkeyvalue.k"
                }
                }
            }
        ]))['keys']

    @property
    def routed_message_keys(self):
        """
        All type of Routed message keys currently stored.

        [Expensive]
        """
        res = next(self.collection.aggregate([
            {
                '$match': {
                    'msg.Routed.body': {
                        '$exists': True
                    }
                }
            }, {
                '$project': {
                    'arrayofkeyvalue': {
                        '$objectToArray': '$msg.Routed.body'
                    }
                }
            }, {
                '$unwind': '$arrayofkeyvalue'
            }, {
                '$group': {
                    '_id': None,
                    'keys': {
                        '$addToSet': '$arrayofkeyvalue.k'
                    }
                }
            }
        ]))['keys']

        return [f'Routed.body.{message_type}' for message_type in res]

    @property
    def message_keys(self):
        return self.direct_message_keys + self.routed_message_keys

    def message_count(self, origin, message_type):
        return self.collection.count({"_origin" : origin, f"msg.{message_type}" : {"$exists" : True}})

    def message_received_bytes(self, origin, message_type):
        res = list(self.collection.aggregate([
            {
                '$match': {
                    'key': 'rx',
                    f'msg.{message_type}' : { '$exists' : True },
                    '_origin' : origin,
                }
            }, {
                '$group': {
                    '_id': None,
                    'total': {
                        '$sum': '$length'
                    }
                }
            }
        ]))

        if len(res) > 0:
            return res[0]['total']
        else:
            return 0

