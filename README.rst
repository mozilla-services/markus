======
Markus
======

Markus is a Python library for generating metrics.

:Code:          https://github.com/mozilla-services/markus
:Issues:        https://github.com/mozilla-services/markus/issues
:License:       MPL v2
:Documentation: http://markus.readthedocs.io/en/latest/


Goals
=====

Markus makes it easier to generate metrics in your program by:

* providing multiple backends (Datadog statsd, statsd, logging, logging rollup,
  and so on) for sending data to different places

* sending metrics to multiple backends at the same time

* providing a testing framework for easy testing

* providing a decoupled architecture making it easier to write code to generate
  metrics without having to worry about making sure creating and configuring a
  metrics client has been done--similar to the Python logging Python logging
  module in this way

I use it at Mozilla in the collector of our crash ingestion pipeline. Peter used
it to build our symbols lookup server, too.


Install
=======

To install Markus, run::

    $ pip install markus

(Optional) To install the requirements for the
``markus.backends.statsd.StatsdMetrics`` backend::

    $ pip install 'markus[statsd]'

(Optional) To install the requirements for the
``markus.backends.datadog.DatadogMetrics`` backend::

    $ pip install 'markus[datadog]'


Quick start
===========

Similar to using the logging library, every Python module can create a
``markus.main.MetricsInterface`` (loosely equivalent to a Python
logging logger) at any time including at module import time and use that to
generate metrics.

For example::

    import markus

    metrics = markus.get_metrics(__name__)


Creating a ``markus.main.MetricsInterface`` using ``__name__``
will cause it to generate all stats keys with a prefix determined from
``__name__`` which is a dotted Python path to that module.

Then you can use the ``markus.main.MetricsInterface`` anywhere in that
module::

    @metrics.timer_decorator("chopping_vegetables")
    def some_long_function(vegetable):
        for veg in vegetable:
            chop_vegetable()
            metrics.incr("vegetable", value=1)


At application startup, configure Markus with the backends you want and any
options they require to publish metrics.

For example, let us configure Markus to publish metrics to the Python logging
infrastructure and Datadog::

    import markus

    markus.configure(
        backends=[
            {
                # Publish metrics to the Python logging infrastructure
                "class": "markus.backends.logging.LoggingMetrics",
            },
            {
                # Publish metrics to Datadog
                "class": "markus.backends.datadog.DatadogMetrics",
                "options": {
                    "statsd_host": "example.com",
                    "statsd_port": 8125,
                    "statsd_namespace": ""
                }
            }
        ]
    )


Once you've added code that publishes metrics, you'll want to test it and make
sure it's working correctly. Markus comes with a ``markus.testing.MetricsMock``
to make testing and asserting specific outcomes easier::

    from markus.testing import MetricsMock


    def test_something():
        with MetricsMock() as mm:
            # ... Do things that might publish metrics

            # Make assertions on metrics published
            mm.assert_incr_once("some.key", value=1)
