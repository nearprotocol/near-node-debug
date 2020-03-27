#!/bin/bash
nohup python3 app.py http://34.80.180.137:3030 > app.out &
child_pid=$!
echo Start process at $child_pid
echo $child_pid > app.pid
