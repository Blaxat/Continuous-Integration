# Distributed Testing Infrastructure

## Overview
A scalable, fault-tolerant distributed testing system designed to monitor repositories, dispatch tests across multiple runners, and aggregate results.

## Video Overview
[![Video Title](https://i9.ytimg.com/vi_webp/291Xu3sskao/mqdefault.webp?sqp=CIi51bwG&rs=AOn4CLCEdsWPTxGXe9uhdCrCMUF0JzRC_Q)](https://youtu.be/291Xu3sskao)

## Components

### 1. Repository Poller (`repo_observer.py`)
- Monitors a specific repository for new commits
- Communicates with dispatcher to initiate test processes
- Continuously checks for repository updates

### 2. Dispatcher (`dispatcher.py`)
- Central coordination service for test distribution
- Manages test runners
- Tracks commit statuses
- Redistributes pending tests

### 3. Test Runner (`runner.py`)
- Executes tests for specific commits
- Registers with dispatcher
- Sends test results back to central service
- Handles disconnection scenarios


## Local Setup

### Clone Repository
   ```bash
   git clone https://github.com/Blaxat/Continuous-Integration.git
   ```

### Local Repository Preparation
1. Create master repository
   ```bash
   mkdir test_repo
   cd test_repo
   git init
   ```

2. Copy tests and commit to master repository
   ```bash
   cp -r /path/to/tests test_repo/
   cd test_repo
   git add tests/
   git commit -m "add tests"
   ```

3. Create repository clones
   ```bash
   # Clone for repository observer
   git clone /path/to/test_repo test_repo_clone_obs
   
   # Clone for test runner
   git clone /path/to/test_repo test_repo_clone_runner
   ```

### Running Locally
1. Start Dispatcher
   ```bash
   python dispatcher.py
   ```

2. Start Test Runner
   ```bash
   python runner.py /path/to/test_repo_clone_runner
   ```

3. Start Repository Poller
   ```bash
   python poll.py /path/to/test_repo_clone_obs
   ```

