# Kafka Monitor

Please check out the official [Scrapy Cluster documentation](http://scrapy-cluster.readthedocs.org/) for more detail on how the Kafka Monitor works.

## Unit Tests

Run the offline unit tests from the `kafka-monitor` folder, not the `tests` folder.

```python
python tests/tests_offline.py -v
```

Once you think you have the kafka-monitor configured properly, run the online unit test to see if it works.

```python
python tests/tests_online.py -v
```