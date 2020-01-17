#!/usr/bin/env python3

import subprocess
from os.path import abspath, expanduser, exists
from os import makedirs
import argparse
import server


"""Stops and removes given docker container."""
def docker_stop_if_exists(name):
    try:
        subprocess.Popen(['docker', 'stop', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except subprocess.CalledProcessError:
        pass
    try:
        subprocess.Popen(['docker', 'rm', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except subprocess.CalledProcessError:
        pass


def start_db(path, port, skip_pull):
    """
    path: Path to connect mongo db to, and store all data.
    port: Port where mongo db service will be listening at.
    skip_pull: Flag to avoid pulling docker image.
    """
    if not skip_pull:
        try:
            print("Downloading mongo image...")
            subprocess.check_output(['docker', 'pull', 'mongo'])
            print("Finished")
        except subprocess.CalledProcessError as exc:
            print("Failed to fetch docker containers: %s" % exc)
            exit(1)

    try:
        print("Spinning up database...")
        if 'neardebug' in subprocess.check_output(['docker', 'ps', '--filter', 'name=neardebug']).decode():
            print("Database already up")
        else:
            path = abspath(expanduser(path))
            if not exists(path):
                makedirs(path)
            try:
                subprocess.check_output(['docker', 'run', '-d', '-p', f'{port}:27017', '-v', f'{path}:/data/db', '--name', 'neardebug', 'mongo'])
                print("Finished")
            except:
                print("\nUnable to launch database\n"\
                        "\nStop hanging container using\n"\
                        "./cli.py --stop\n"\
                    )
                exit(0)

    except subprocess.CalledProcessError as exc:
        print("Failed to start docker container: %s" % exc)
        exit(1)

    print("NEAR Diagnostic Tool started.")
    print(f"Connect to: http://0.0.0.0:{port}")


def watch(logs, port):
    if not logs:
        return

    db = server.DBAccess(f'127.0.0.1:{port}', 'diagnostic')
    for log in logs.split(','):
        handler = db.handler(log)
        server.Collector(open(log), handler).start()


def stop():
    docker_stop_if_exists('neardebug')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Near node debug app')

    parser.add_argument('--path', default='~/.near-diagnostics', help="Database with logs will be stored at this place.")
    parser.add_argument('--port', type=int, default=27017, help="Database will be listening at this port.")
    parser.add_argument('--stop', action='store_true', help="Stop database")
    parser.add_argument('--skip_pull', action='store_true', help="Don't try to pull docker image. Use only if image is already downloaded.")
    parser.add_argument('--watch', default='', help='Output files to observe')

    args = parser.parse_args()

    if args.stop:
        stop()
    else:
        start_db(args.path, args.port,args.skip_pull)
        watch(args.watch, args.port)
