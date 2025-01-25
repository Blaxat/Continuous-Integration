import argparse
import subprocess
import os
import socket
import time
import helpers
from datetime import datetime

def poll(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatcher_address", 
                        help="dispatcher host:port, by default it uses localhost:8000",
                        default="localhost:8000",
                        action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="path to the repository this will observe")
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_address.split(":")
    print(dispatcher_host + ':' +dispatcher_port)

    while True:
        try:
            subprocess.check_output(['./update_repo.sh', args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception("Could not update and check repository. " +
             "Reason: %s" % e.output)

        
        commit_path=".commit_id"
        if os.path.isfile(commit_path):
            try:
                response = helpers.communicate(dispatcher_host, int(dispatcher_port), "status")
            except socket.error as e:
                raise Exception('Error occured while communicating with dispatcher, reason: %s' % e)

            if response == "OK":
                with open(commit_path, "r") as f:
                    commitID = f.readline()
                    current_time = datetime.now().strftime("%H:%M:%S")
                    print('New commit observed: %s at %s' % (commitID, current_time))
                    try: 
                        response = helpers.communicate(dispatcher_host, int(dispatcher_port), "dispatch:%s" % commitID)
                        if response != "OK":
                            raise Exception("Could not dispatch the test: %s" % response)
                    except socket.error as e:
                        raise Exception('Error occured while communicating with dispatcher, reason: %s' % e)                
            else:
                raise Exception("Could not dispatch the test: %s" % response)
        time.sleep(5)
                 


if __name__ == "__main__":
    poll()



