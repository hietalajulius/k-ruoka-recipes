![](https://github.com/hietalajulius/k-ruoka-recipes/blob/master/cover.gif?raw=true)



Junction project directory

## Setup

1. Add execution permissions to **run.py**: \
  `chmod +x run.py`

2. Install **run.py** dependencies: \
  `pip install run_requirements.txt`

## Building, running etc.

Build all containers: \
  `./run.py build`

Build specific containers (comma-separated): \
  `./run.py build --services=webapp`

Run containers: \
  `./run.py run --services=possu`

Run whole system: \
  `./run.py compose` or `docker-compose up` \
then open [http://localhost:80](http://localhost:80)

Check running containers: \
  `docker ps`

Clean up (remove running containers etc.): \
  `./run.py cleanup`
