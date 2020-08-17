# fullmoon
interact with teapot server and records data

## Getting started
1. install docker and docker-compose
2. clone this repository
3. run the init.sh to create the docker_mount dir
4. update the config.py as necessary
4. run docker-compose.yaml

## services
* record - periodically collect and stores dc values and lux values from rpi devices running teapot server
* control - change the led brightness as required
