import argparse
import threading
import socketserver
import re
import helpers
import time
import socket
import os
from datetime import datetime


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.runners = []
        self.dead = False
        self.dispatched_commits = {}
        self.pending_commits = []
        self.lock = threading.Lock()


class DispatcherHandler(socketserver.BaseRequestHandler):
    command_re = re.compile(r"(.\w+)(:.+)*")
    def handle(self):
        self.data = self.request.recv(1024).strip()
        self.data = self.data.decode('utf-8')
        command_groups = self.command_re.match(self.data)
        if not command_groups:
            response = "Invalid Request"  
            self.request.sendall(response.encode('utf-8')) 
            return
        command = command_groups.group(1)

        if command == "status":
            response = "OK"  
            self.request.sendall(response.encode('utf-8')) 
        
        elif command == "dispatch":
            try:
                commitID = command_groups.group(2)[1:]
                current_time = datetime.now().strftime("%H:%M:%S")
                print('New commitID received at %s' % (current_time))
                with self.server.lock:
                    self.server.pending_commits.append(commitID)
                    print("ARR: %s" % (commitID))
                response = "OK"
            except Exception as e:
                print("Error while reading commit %s: %s" % (commitID, e))
                response = "ERROR"
            finally:
                self.request.sendall(response.encode('utf-8'))

        elif command == "register":
            address = command_groups.group(2)[1:]
            address_match = re.match(r":([^:]+):([^:]+)", address)
            if not address_match:
                response = "Invalid address format"
                self.request.sendall(response.encode('utf-8'))
                return
            host, port = address_match.groups()
            runner = {"host": host, "port": port}
            with self.server.lock:
                self.server.runners.append(runner)
            current_time = datetime.now().strftime("%H:%M:%S")
            print("Registered a Runner %s: %s at :%s" % (host, int(port), current_time))
            response = "OK"  
            self.request.sendall(response.encode('utf-8'))
        
        elif command == "results":
            resp = command_groups.group(2)[1:].split(":")
            commitID = resp[0]
            outLen = resp[1]
            leftOvers = 1024 - (len(command) + len(commitID) + len(outLen) + 3)
            if leftOvers < int(outLen):
                self.data += self.request.recv(outLen-leftOvers).strip()
            message = self.data
            output = message.split(":")[3:]
            output = "\n".join(output)
            current_time = datetime.now().strftime("%H:%M:%S")
            print("Test Results for commit %s: received at %s" % (commitID, current_time))
            with self.server.lock:
                if commitID in self.server.dispatched_commits:
                    del self.server.dispatched_commits[commitID]
                    print(f"REMOVED_DIS: {commitID}")
                if commitID in self.server.pending_commits:
                    self.server.pending_commits.remove(commitID)
                    print(f"REMOVED: {commitID}")
            if not os.path.exists("test_results"):
                os.makedirs("test_results")
            with open("test_results/%s" % commitID, "w") as f:
                with self.server.lock:
                    f.write(output)
            response = "OK"  
            self.request.sendall(response.encode('utf-8'))
            

def runner_checker(server):
    def manage_runner(runner):
        with server.lock:
            for commit, r in server.dispatched_commits.items():
                if runner == r:
                    if commit in server.dispatched_commits:
                        del server.dispatched_commits[commit]
                    if commit not in server.pending_commits:
                        server.pending_commits.append(commit)
                    break
        server.runners.remove(runner)

    while not server.dead:
        for runner in server.runners:
            try: 
                response = helpers.communicate(runner['host'], int(runner['port']), "ping")
                if(response != "pong"):
                   print("Runner: %s:%s is not responding" % (runner['host'], int(runner['port'])))
                   manage_runner(runner)
            except socket.error:
                print("Runner: %s:%s disconnected" % (runner['host'], int(runner['port'])))
                manage_runner(runner)
        time.sleep(1)


def redestribute(server):
    while not server.dead:
        for commit in server.pending_commits:
            dispatch_commit(commit, server)
    time.sleep(5)


def dispatch_commit(commit, server):
        if len(server.runners) == 0:
            return
        
        for runner in server.runners:
            try: 
                current_time = datetime.now().strftime("%H:%M:%S")
                print('Dispatched commitID:%s to runner:%s:%s at %s' % (commit, runner['host'], int(runner['port']), current_time))
                with server.lock:
                    if commit not in server.dispatched_commits:
                        server.dispatched_commits[commit] = runner
                    if commit in server.pending_commits:
                        server.pending_commits.remove(commit)
                response = helpers.communicate(runner['host'], int(runner['port']), "runtest:%s" % commit)
                if response != "OK":
                    print(f"RESP: {response}")
                    with server.lock:
                        if commit in server.dispatched_commits:
                            del server.dispatched_commits[commit]
                        if commit not in server.pending_commits:
                            server.pending_commits.append(commit)
                return
            except socket.error:
                print("Runner: %s:%s disconnected" % (runner['host'], int(runner['port'])))

            
def start_server():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", 
                        help="Mention dispatcher server's host",
                        default="localhost",
                        action="store")
    parser.add_argument("--port",
                        help="Mention dispatcher server's host",
                        default=8000,
                        action="store")  
    args = parser.parse_args()

    server = ThreadingTCPServer((args.host, int(args.port)), DispatcherHandler)
    print ('serving on %s:%s' % (args.host, int(args.port)))

    runner_heartbeat = threading.Thread(target=runner_checker, args=(server,))
    redestributor = threading.Thread(target=redestribute, args=(server,))

    try:
        runner_heartbeat.start()
        redestributor.start()
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True
        runner_heartbeat.join()
        server.shutdown()
        redestributor.join()


if __name__ == "__main__":
    start_server()
