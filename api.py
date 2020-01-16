import server

class DBApi(server.DBAccess):
    pass

# TODO: Parse time from logs
# TODO: Make a tool that shows the graph (ideally at different points in time)
# TODO: Make a tool to see all types of message passing, size, number of messages, edges.
# TODO: Try to make a benchmark to see how much slow does the node becomes with diagnostic enabled.
# TODO: Make a pytest using this tool (download this library from github).
# TODO: Find how slow is routing table right now.
# TODO: Use this tool to spawn 100 nodes on different machines and report to a single DB
#  This is just allowing to run a database in waiting mode
#  And letting each node know where to post all logs
#  We will have access in realtime to network behavior
