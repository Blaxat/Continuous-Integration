import argparse
import socketserver
import socket
import threading
import re
import helpers
import subprocess


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.dispatcher = None
        self.repo = None
        self.busy = False
        self.dead = False
        self.pending_results = {}
        self.lock = threading.Lock()


class RunnerHandler(socketserver.BaseRequestHandler):
    command_re = re.compile(r"(.\w+)(:.+)*")

    def runtests(self, commitID, repo):
        try:
            subprocess.check_output(['./test_repo.sh', repo, commitID])
            with open("results", "r") as result_file:
                output = result_file.read()
                try:
                    helpers.communicate(
                        self.server.dispatcher["host"],
                        int(self.server.dispatcher["port"]),
                        f"results:{commitID}:{len(output)}:{output}"
                    )
                    print(f"Test results of {commitID} are sent to dispatcher")
                    return "OK"
                except socket.error:
                    with self.server.lock:
                        if commitID not in self.server.pending_results:
                            self.server.pending_results[commitID] = output
                    print("Dispatcher isn't active")
                    return "Failed"
        except subprocess.CalledProcessError as e:
            print(f"Subprocess Error: {e}")
            return "Failed"

    def handle(self):
        self.data = self.request.recv(1024).strip()
        self.data = self.data.decode('utf-8')
        command_groups = self.command_re.match(self.data)
        if not command_groups:
            response = "Invalid Request"
            self.request.sendall(response.encode('utf-8'))
            return

        command = command_groups.group(1)

        if command == "ping":
            threading.Thread(target=resender, args=(self.server,), daemon=True).start()
            response = "pong"
            self.request.sendall(response.encode('utf-8'))

        if command == "runtest":
            threading.Thread(target=resender, args=(self.server,), daemon=True).start()
            print(f"Is Server busy?: {self.server.busy}")
            if self.server.busy:
                response = "BUSY"
                self.request.sendall(response.encode('utf-8'))
                return
            with self.server.lock:
                self.server.busy = True

            commitID = command_groups.group(2)[1:]
            print(f"Running tests on commit: {commitID}")
            response = self.runtests(commitID, self.server.repo)
            with self.server.lock:
                self.server.busy = False

            self.request.sendall(response.encode('utf-8'))


def resender(server):
    with server.lock:
        for commitID, output in list(server.pending_results.items()):
            try:
                helpers.communicate(
                    server.dispatcher["host"],
                    int(server.dispatcher["port"]),
                    f"results:{commitID}:{len(output)}:{output}"
                )
                print(f"Test results of {commitID} are sent to dispatcher")
                del server.pending_results[commitID]
            except socket.error as e:
                print(f"Error occurred while connecting to dispatcher: {e}")


def start_server():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dispatcher_address",
        help="dispatcher host:port, by default it uses localhost:8000",
        default="localhost:8000",
        action="store"
    )
    parser.add_argument(
        "--runner_address",
        help="runner host:port, by default it uses localhost:8100",
        default="localhost:8100",
        action="store"
    )
    parser.add_argument(
        "repo",
        metavar="REPO",
        type=str,
        help="path to the repository this will run tests on"
    )
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_address.split(":")
    runner_host, runner_port = args.runner_address.split(":")

    server = ThreadingTCPServer((runner_host, int(runner_port)), RunnerHandler)
    print(f'Serving on {runner_host}:{int(runner_port)}')

    try:
        response = helpers.communicate(dispatcher_host, int(dispatcher_port), "status")
        if response == "OK":
            try:
                message = f"register::{runner_host}:{int(runner_port)}"
                response = helpers.communicate(dispatcher_host, int(dispatcher_port), message)
                if response != "OK":
                    raise Exception(response)
            except socket.error as e:
                raise Exception(f"Cannot register this runner, reason: {e}")
    except (socket.error, KeyboardInterrupt) as e:
        raise Exception(f"Error occurred while communicating with dispatcher, reason: {e}")

    server.dispatcher = {'host': dispatcher_host, 'port': int(dispatcher_port)}
    server.repo = args.repo

    try:
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True


if __name__ == "__main__":
    start_server()
