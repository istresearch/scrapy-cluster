# Scrapy Cluster Documentation

You can follow [this](http://docs.readthedocs.org/en/latest/getting_started.html#in-rst) guide on readthedocs to get your own local documentation up and running.

Otherwise, it boils down to the following commands

```bash
$ pip install sphinx sphinx-autobuild sphinx-rtd-theme
$ cd docs
$ sphinx-build . _build_html
$ sphinx-autobuild . _build_html

Serving on http://127.0.0.1:8000
...
```

You will now be able to view the documentation as you live edit it on your machine.
