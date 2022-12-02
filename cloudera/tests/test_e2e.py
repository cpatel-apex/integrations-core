import pytest

from datadog_checks.cloudera import ClouderaCheck
from datadog_checks.cloudera.metrics import METRICS


@pytest.mark.e2e
def test_e2e(dd_agent_check, instance):
    # Given
    instance['api_url'] = "http://localhost:8080/api/v48"
    # When
    aggregator = dd_agent_check(instance)
    # Then
    for category, metrics in METRICS.items():
        for metric in metrics:
            aggregator.assert_metric(f'cloudera.{category}.{metric}')
    aggregator.assert_service_check('cloudera.can_connect', ClouderaCheck.OK)
    aggregator.assert_service_check('cloudera.cluster.health', ClouderaCheck.CRITICAL, message="BAD_HEALTH")  # test env is in BAD_HEALTH
    aggregator.assert_service_check('cloudera.host.health', ClouderaCheck.OK)
