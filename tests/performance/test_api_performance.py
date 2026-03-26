import statistics
import time

import pytest


def _measure_ms(callable_obj):
    start = time.perf_counter()
    callable_obj()
    return (time.perf_counter() - start) * 1000


@pytest.mark.performance
def test_health_endpoint_latency_profile(api_call):
    runs = 10
    samples = [_measure_ms(lambda: api_call("GET", "/health")) for _ in range(runs)]

    avg_ms = statistics.mean(samples)
    p95_ms = sorted(samples)[int(len(samples) * 0.95) - 1]

    print(f"health latency(ms) avg={avg_ms:.2f}, p95={p95_ms:.2f}, samples={samples}")

    # 宽松阈值：主要用于发现明显退化，而非微基准压测
    assert avg_ms < 1000
    assert p95_ms < 2000


@pytest.mark.performance
@pytest.mark.requires_admin
def test_group_list_latency_profile(api_call, admin_session):
    runs = 10
    headers = admin_session["headers"]
    samples = [_measure_ms(lambda: api_call("GET", "/groups", headers=headers)) for _ in range(runs)]

    avg_ms = statistics.mean(samples)
    p95_ms = sorted(samples)[int(len(samples) * 0.95) - 1]

    print(f"groups latency(ms) avg={avg_ms:.2f}, p95={p95_ms:.2f}, samples={samples}")

    assert avg_ms < 1500
    assert p95_ms < 3000
