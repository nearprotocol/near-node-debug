#!/usr/bin/env python

import subprocess
from os.path import abspath, expanduser, exists
from os import makedirs
from app import start_server
import argparse


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


def run(web_port, database_path, database_port, skip_database, skip_pull, debug):
    if skip_database:
        skip_pull = True

    if not skip_pull:
        try:
            print("Downloading mongo image...")
            subprocess.check_output(['docker', 'pull', 'mongo'])
            print("Finished")
        except subprocess.CalledProcessError as exc:
            print("Failed to fetch docker containers: %s" % exc)
            exit(1)

    if not skip_database:
        try:
            print("Spinning up database")
            if 'neardebug' in subprocess.check_output(['docker', 'ps', '--filter', 'name=neardebug']).decode():
                print("Database already up")
            else:
                database_path = abspath(expanduser(database_path))
                if not exists(database_path):
                    makedirs(database_path)
                subprocess.check_output(['docker', 'run', '-d', '-p', f'{database_port}:27017', '-v', f'{database_path}:/data/db', '--name', 'neardebug', 'mongo'])
            print("Finished")
        except subprocess.CalledProcessError as exc:
            print("Failed to start docker container: %s" % exc)
            exit(1)

    print("NEAR debug app started.")
    print(f"Connect via http://0.0.0.0:{database_port}")
    start_server(web_port, debug, 'near_debug', f'localhost:{database_port}')


def stop():
    docker_stop_if_exists('neardebug')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Near node debug app')

    parser.add_argument('--web_port', type=int, default=8181, help="App will be listening at this port. Point debug telemetry to it. Default 8181.")
    parser.add_argument('--database_path', default='~/.near-debug-data', help="Database with logs will be stored at this place.")
    parser.add_argument('--database_port', type=int, default=27017, help="Database will be listening at this port.")
    parser.add_argument('--skip_database', action='store_true', help="Don't spin up database. Use only if database is already up.")
    parser.add_argument('--skip_pull', action='store_true', help="Don't try to pull docker image. Use only if image is already downloaded.")
    parser.add_argument('--debug', action='store_true', help="Flask debug active")
    parser.add_argument('--stop', action='store_true', help="Stop database")

    args = parser.parse_args()

    if args.stop:
        stop()
    else:
        run(args.web_port, args.database_path, args.database_port, args.skip_database, args.skip_pull, args.debug)
