import pytest

from datadog_checks.envoy import Envoy

from .common import DEFAULT_INSTANCE, FLAKY_METRICS, PROMETHEUS_METRICS, requires_new_environment

pytestmark = [requires_new_environment]


@pytest.mark.e2e
def test_e2e(dd_agent_check):
    aggregator = dd_agent_check(DEFAULT_INSTANCE, rate=True)

    for metric in PROMETHEUS_METRICS:
        formatted_metric = "envoy.{}".format(metric)
        if metric in FLAKY_METRICS:
            aggregator.assert_metric(formatted_metric, at_least=0)
            continue
        aggregator.assert_metric(formatted_metric)
    aggregator.assert_service_check('envoy.openmetrics.health', Envoy.OK)
