import os
import unittest
import subprocess

def test_commit():
    try:
        subprocess.check_output(['./test_repo.sh', "/mnt/d/VS_ CODE/New folder/CI/runner_clone", "fbb994df2bb7c80200971c0a97692e9668650bbc"])
    except subprocess.CalledProcessError as e:
        print(f"Folder might not exist: {e}")
    return

if __name__ == '__main__':
    test_commit()