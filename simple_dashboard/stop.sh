#!/bin/bash
kill -9 $(cat app.pid)
rm app.pid
