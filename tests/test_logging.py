# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime

from markus.backends.logging import LoggingMetrics, LoggingRollupMetrics
from markus.main import MetricsFilter, MetricsRecord


class TestLoggingMetrics:
    def test_incr(self, caplog):
        caplog.set_level("DEBUG")
        rec = MetricsRecord("incr", key="foo", value=10, tags=["key1:val", "key2:val"])
        lm = LoggingMetrics()
        lm.emit_to_backend(rec)
        assert caplog.record_tuples == [
            ("markus", 20, "METRICS|incr|foo|10|#key1:val,key2:val")
        ]

    def test_gauge(self, caplog):
        caplog.set_level("DEBUG")
        rec = MetricsRecord(
            "gauge", key="foo", value=100, tags=["key1:val", "key2:val"]
        )
        lm = LoggingMetrics()
        lm.emit_to_backend(rec)
        assert caplog.record_tuples == [
            (
                "markus",
                20,
                "METRICS|gauge|foo|100|#key1:val,key2:val",
            )
        ]

    def test_timing(self, caplog):
        caplog.set_level("DEBUG")
        rec = MetricsRecord(
            "timing", key="foo", value=1234, tags=["key1:val", "key2:val"]
        )
        lm = LoggingMetrics()
        lm.emit_to_backend(rec)
        assert caplog.record_tuples == [
            (
                "markus",
                20,
                "METRICS|timing|foo|1234|#key1:val,key2:val",
            )
        ]

    def test_histogram(self, caplog):
        caplog.set_level("DEBUG")
        rec = MetricsRecord(
            "histogram", key="foo", value=4321, tags=["key1:val", "key2:val"]
        )
        lm = LoggingMetrics()
        lm.emit_to_backend(rec)
        assert caplog.record_tuples == [
            (
                "markus",
                20,
                "METRICS|histogram|foo|4321|#key1:val,key2:val",
            )
        ]

    def test_filters(self, caplog):
        class BlueFilter(MetricsFilter):
            def filter(self, record):
                if "blue" not in record.key:
                    return
                return record

        caplog.set_level("DEBUG")
        lm = LoggingMetrics(filters=[BlueFilter()])
        lm.emit_to_backend(MetricsRecord("incr", key="foo", value=1, tags=[]))
        lm.emit_to_backend(MetricsRecord("incr", key="foo.blue", value=2, tags=[]))
        assert caplog.record_tuples == [("markus", 20, "METRICS|incr|foo.blue|2|")]

    def test_utc_timezone_incr(self, caplog, time_machine):
        time_machine.move_to("2017-03-06T16:30:00+00:00", tick=False)
        caplog.set_level("DEBUG")
        rec = MetricsRecord("incr", key="foo", value=10, tags=["key1:val", "key2:val"])
        lm = LoggingMetrics(options={"timestamp_mode": "utc"})
        lm.emit_to_backend(rec)
        assert caplog.record_tuples == [
            (
                "markus",
                20,
                "METRICS|2017-03-06T16:30:00+00:00|incr|foo|10|#key1:val,key2:val",
            )
        ]

    def test_local_timezone_incr(self, caplog, time_machine):
        time_machine.move_to("2017-03-06 16:30:00", tick=False)
        caplog.set_level("DEBUG")
        rec = MetricsRecord("incr", key="foo", value=10, tags=["key1:val", "key2:val"])
        lm = LoggingMetrics(options={"timestamp_mode": "local"})
        lm.emit_to_backend(rec)
        assert caplog.record_tuples == [
            ("markus", 20, "METRICS|2017-03-06T16:30:00|incr|foo|10|#key1:val,key2:val")
        ]


class TestLoggingRollupMetrics:
    def test_rollup(self, caplog, time_machine):
        caplog.set_level("DEBUG")

        time_machine.move_to(
            datetime.datetime(2017, 4, 19, 12, 0, 0, tzinfo=datetime.timezone.utc),
            tick=False,
        )
        lm = LoggingRollupMetrics()
        lm.emit_to_backend(MetricsRecord("incr", key="foo", value=1, tags=None))
        lm.emit_to_backend(MetricsRecord("incr", key="foo", value=1, tags=None))
        lm.emit_to_backend(MetricsRecord("gauge", key="widget", value=10, tags=None))
        lm.emit_to_backend(MetricsRecord("incr", key="foo", value=1, tags=None))
        lm.emit_to_backend(MetricsRecord("incr", key="bar", value=1, tags=None))
        lm.emit_to_backend(MetricsRecord("gauge", key="widget", value=20, tags=None))
        lm.emit_to_backend(MetricsRecord("gauge", key="widget", value=5, tags=None))
        lm.emit_to_backend(
            MetricsRecord("histogram", key="save_time", value=50, tags=None)
        )
        lm.emit_to_backend(
            MetricsRecord("histogram", key="save_time", value=60, tags=None)
        )

        time_machine.move_to(
            datetime.datetime(2017, 4, 19, 12, 0, 11, tzinfo=datetime.timezone.utc),
            tick=False,
        )
        lm.emit_to_backend(MetricsRecord("incr", key="bar", value=1, tags=None))

        assert caplog.record_tuples == [
            ("markus", 20, "ROLLUP INCR bar: count:1|rate:1/10"),
            ("markus", 20, "ROLLUP INCR foo: count:3|rate:3/10"),
            ("markus", 20, "ROLLUP GAUGE widget: count:3|current:5|min:5|max:20"),
            (
                "markus",
                20,
                "ROLLUP HISTOGRAM save_time: "
                "count:2|min:50.00|avg:55.00|median:55.00|ninety-five:60.00|max:60.00",
            ),
        ]
