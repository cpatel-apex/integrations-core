import os

from datadog_checks.dev import get_docker_hostname, get_here

HOST = get_docker_hostname()
PORT = 7180

INSTANCE = {
    'workload_username': '~',
    'workload_password': '~',
    'api_url': 'http://localhost:8080/api/v48/',
    'tags': ['test1'],
}

HERE = get_here()
COMPOSE_FILE = os.path.join(HERE, 'docker', 'docker-compose.yaml')

CAN_CONNECT_TAGS = [
    'api_url=http://localhost:8080/api/v48/',
    'test1',
]
CLUSTER_HEALTH_TAGS = [
    '_cldr_cb_clustertype:Data Hub',
    '_cldr_cb_origin:cloudbreak',
    'cloudera_cluster:cod--qfdcinkqrzw',
    'test1',
]
