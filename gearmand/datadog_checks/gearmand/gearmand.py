# (C) Datadog, Inc. 2013-present
# (C) Patrick Galbraith <patg@patg.net> 2013
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

from six import PY2

from datadog_checks.base import AgentCheck

# Python 3 compatibility is a different library
# It's a drop in replacement but has a different name
# This will enable the check to use the new library
if PY2:
    import gearman
else:
    import python3_gearman as gearman

MAX_NUM_TASKS = 200


class Gearman(AgentCheck):
    SERVICE_CHECK_NAME = 'gearman.can_connect'
    gearman_clients = {}

    def get_library_versions(self):
        return {"gearman": gearman.__version__}

    def _get_client(self, host, port):
        if not (host, port) in self.gearman_clients:
            self.log.debug("Connecting to gearman at address %s:%s", host, port)
            self.gearman_clients[(host, port)] = gearman.GearmanAdminClient(["%s:%s" % (host, port)])

        return self.gearman_clients[(host, port)]

    def _get_aggregate_metrics(self, tasks, workers, tags):
        running = 0
        queued = 0

        for stat in tasks:
            running += stat['running']
            queued += stat['queued']

        unique_tasks = len(tasks)

        self.gauge("gearman.unique_tasks", unique_tasks, tags=tags)
        self.gauge("gearman.running", running, tags=tags)
        self.gauge("gearman.queued", queued, tags=tags)
        self.gauge("gearman.workers", workers, tags=tags)

        self.log.debug("running %d, queued %d, unique tasks %d, workers: %d", running, queued, unique_tasks, workers)

    def _get_per_task_metrics(self, tasks, task_filter, tags):
        if len(task_filter) > MAX_NUM_TASKS:
            self.warning("The maximum number of tasks you can specify is %s.", MAX_NUM_TASKS)

        if not len(task_filter) == 0:
            tasks = [t for t in tasks if t['task'] in task_filter]

        if len(tasks) > MAX_NUM_TASKS:
            # Display a warning in the info page
            self.warning(
                (
                    "Too many tasks to fetch. "
                    "You must choose the tasks you are interested in by editing the gearmand.yaml configuration file "
                    "or get in touch with Datadog support"
                )
            )

        for stat in tasks[:MAX_NUM_TASKS]:
            running = stat['running']
            queued = stat['queued']
            workers = stat['workers']

            task_tags = tags[:]
            task_tags.append("task:{}".format(stat['task']))
            self.gauge("gearman.running_by_task", running, tags=task_tags)
            self.gauge("gearman.queued_by_task", queued, tags=task_tags)
            self.gauge("gearman.workers_by_task", workers, tags=task_tags)

    def _get_conf(self, instance):
        host = instance.get('server', None)
        port = instance.get('port', None)
        tasks = instance.get('tasks', [])

        if host is None:
            self.warning("Host not set, assuming 127.0.0.1")
            host = "127.0.0.1"

        if port is None:
            self.warning("Port is not set, assuming 4730")
            port = 4730

        tags = instance.get('tags', [])

        return host, port, tasks, tags

    def check(self, instance):
        self.log.debug("Gearman check start")

        host, port, task_filter, instance_tags = self._get_conf(instance)

        tags = ["server:{0}".format(host), "port:{0}".format(port)] + instance_tags

        client = self._get_client(host, port)
        self.log.debug("Connected to gearman")

        try:
            tasks = client.get_status()
            workers = len([w for w in client.get_workers() if w['tasks']])
            self._get_aggregate_metrics(tasks, workers, tags)
            self._get_per_task_metrics(tasks, task_filter, tags)
            self.service_check(
                self.SERVICE_CHECK_NAME,
                AgentCheck.OK,
                tags=tags,
            )
        except Exception as e:
            self.service_check(self.SERVICE_CHECK_NAME, AgentCheck.CRITICAL, message=str(e), tags=tags)
            raise

        if self.is_metadata_collection_enabled():
            self._collect_metadata(client)

    def _collect_metadata(self, client):
        try:
            resp = client.get_version()
        except Exception as e:
            self.log.warning('Error retrieving version information: %s', e)
            return

        if not resp.startswith('OK '):
            self.log.warning('Error retrieving version information from server, response: %s', resp)
            return

        # strip off the 'OK ' text
        server_version = resp[3:]
        if server_version:
            self.set_metadata('version', server_version)
