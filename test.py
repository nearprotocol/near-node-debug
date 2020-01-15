import collector
import server

LOG = '/home/marx/Documents/near/projects/cryptonear/nearcore/output/output{}.log'
db = server.DBAccess('0.0.0.0:27017', 'diagnostic')

for i in range(4):
    log = LOG.format(i)
    handler = db.handler(f'node{i}')
    collector.Collector(open(log), handler).start()
