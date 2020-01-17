from server import DBAccess
from api import Api
from bson.code import Code

db = DBAccess("localhost:27017", "diagnostic")

api = Api(db)

print(api.total_entries)
print(api.logs_origin)
print(api.keys)
print(api.message_keys)


def traffic_stats(api):
    for message_type in api.message_keys:
        for origin in api.logs_origin:
            print(origin, message_type, api.message_count(origin, message_type), api.message_received_bytes(origin, message_type))


traffic_stats(api)
