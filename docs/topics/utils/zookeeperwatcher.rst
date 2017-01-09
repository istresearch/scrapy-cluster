.. _zookeeper_watcher:

Zookeeper Watcher
=================

The Zookeeper Watcher utility class is a `circuit breaker <https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern>`_ design pattern around `Apache Zookeeper <http://zookeeper.apache.org>`_ that allows you to watch a one or two files in order to be notified when when they are updated. The circuit breaker allows your application the ability to function normally while your connection is interrupted to Zookeeper, and reestablish the connection and watches automatically.

Behind the scenes, the Zookeeper Watcher utility uses `kazoo <http://kazoo.readthedocs.org/>`_, and extends Kazoo's functionality by allowing automatic reconnection, automatic file watch reestablishment, and management.

In practice, the Zookeeper Watcher is used to watch configuration files stored within Zookeeper, so that your application may update its configuration automatically. In two-file mode, the utility assumes the first file it is watching actually has a full path to another Zookeeper file where the actual configuration is stored, enabling you to dynamically switch to distinct configurations files stored in Zookeeper as well as see updates to those files.

Within this configuration file watcher, the Zookeeper Watcher also has the ability to function in both **event driven** and **polling mode** (or a combination thereof). Depending on your application setup, it may be more beneficial to use one or the other types of modes.

.. class:: ZookeeperWatcher (hosts, filepath, valid_handler=None, config_handler=None, error_handler=None, pointer=False, ensure=False, valid_init=True)

    Zookeeper file watcher, used to tell a program their Zookeeper file has changed. Can be used to watch a single file, or both a file and path of its contents. Manages all connections, drops, reconnections for you.

    :param str hosts: The zookeeper hosts to use
    :param str filepath: The full path to the file to watch
    :param func valid_handler: The method to call for a 'is valid' state change
    :param func config_handler: The method to call when a content change occurs
    :param func error_handler: The method to call when an error occurs
    :param bool pointer: Set to true if the file contents are actually a path to another zookeeper file, where the real config resides
    :param bool ensure: Set to true for the ZookeeperWatcher to create the watched file if none exists
    :param bool valid_init: Ensure the client can connect to Zookeeper first try

    .. method:: is_valid()

        :returns: A boolean indicating if the current series of watched files is valid. Use this for basic polling usage.

    .. method:: get_file_contents(pointer=False)

        Gets any file contents you care about. Defaults to the main file

        :param bool pointer: Get the contents of the file pointer, not the pointed at file
        :returns: A string of the contents

    .. method:: ping()

        A ping to determine if the Zookeeper connection is working

        :returns: True if the connection is alive, otherwise False

    .. method:: close(kill_restart=True)

        Gracefully shuts down the Zookeeper Watcher

        :param kill_restart: Set to False to allow the daemon process to respawn. This parameter is not recommended and may be deprecated in future versions.

Usage
-----

The Zookeeper Watcher spawns a daemon process that runs in the background along side your application, so you only need to initialize and keep the variable around in your program.

Assuming you have pushed some kind of content into Zookeeper already, for example ``stuff here`` or ``Some kind of config string here``.

In polling mode:

::

    >>> from scutils.zookeeper_watcher import ZookeeperWatcher
    >>> from time import sleep
    >>> file = "/tmp/myconfig"
    >>> zoo_watcher = ZookeeperWatcher("scdev", file)
    >>> hosts = "scdev"
    >>> zoo_watcher = ZookeeperWatcher(hosts, file)
    >>> while True:
    ...      print "Valid File?", zoo_watcher.is_valid()
    ...      print "Contents:", zoo_watcher.get_file_contents()
    ...      sleep(1)
    ...
    Valid File? True
    Contents: stuff here
    Valid File? True
    Contents: stuff here

For event driven polling, you need to define any of the three event handlers within your application. The below example defines only the the ``config_handler``, which allows you to monitor changes to your desired file.

::

    >>> from scutils.zookeeper_watcher import ZookeeperWatcher
    >>> from time import sleep
    >>> file = "/tmp/myconfig"
    >>> def change_file(conf_string):
    ...     print "Your file contents:", conf_string
    ...
    >>> zoo_watcher = ZookeeperWatcher("scdev", file, config_handler=change_file)
    Your file contents: Some kind of config string here

You can manually alter your file contents if you have access to the Zookeeper's command line interface, but otherwise can use the ``file_pusher.py`` file located within the ``crawling/config`` directory of this project. For more information about the ``file_pusher.py`` script and its uses, please see :ref:`here <domain_specific_configuration>`.

Example
-------

In this example, we will create a fully functional file watcher that allows us to flip between various states of usage by passing different command line arguments.

::

    from scutils.zookeeper_watcher import ZookeeperWatcher
    from time import sleep
    import argparse

    parser = argparse.ArgumentParser(
                description="Zookeeper file watcher")
    parser.add_argument('-z', '--zoo-keeper', action='store', required=True,
                        help="The Zookeeper connection <host>:<port>")
    parser.add_argument('-f', '--file', action='store', required=True,
                        help="The full path to the file to watch in Zookeeper")
    parser.add_argument('-p', '--pointer', action='store_const', const=True,
                        help="The file contents point to another file")
    parser.add_argument('-s', '--sleep', nargs='?', const=1, default=1,
                        type=int, help="The time to sleep between poll checks")
    parser.add_argument('-v', '--valid-init', action='store_false',
                        help="Do not ensure zookeeper is up upon initial setup",
                        default=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--poll', action='store_true', help="Polling example")
    group.add_argument('--event', action='store_true',
                       help="Event driven example")

    args = vars(parser.parse_args())

    hosts = args['zoo_keeper']
    file = args['file']
    pointer = args['pointer']
    sleep_time = args['sleep']
    poll = args['poll']
    event = args['event']
    valid = args['valid_init']

    def valid_file(state):
        print "The valid state is now", state

    def change_file(conf_string):
        print "Your file contents:", conf_string

    def error_file(message):
        print "An error was thrown:", message

    # You can use any or all of these, polling + handlers, some handlers, etc
    if pointer:
        if poll:
            zoo_watcher = ZookeeperWatcher(hosts, file, ensure=True,pointer=True)
        elif event:
            zoo_watcher = ZookeeperWatcher(hosts, file,
                                           valid_handler=valid_file,
                                           config_handler=change_file,
                                           error_handler=error_file,
                                           pointer=True, ensure=True, valid_init=valid)
    else:
        if poll:
            zoo_watcher = ZookeeperWatcher(hosts, file, ensure=True)
        elif event:
            zoo_watcher = ZookeeperWatcher(hosts, file,
                                           valid_handler=valid_file,
                                           config_handler=change_file,
                                           error_handler=error_file,
                                           valid_init=valid, ensure=True)

    print "Use a keyboard interrupt to shut down the process."
    try:
        while True:
            if poll:
                print "Valid File?", zoo_watcher.is_valid()
                print "Contents:", zoo_watcher.get_file_contents()
            sleep(sleep_time)
    except:
        pass
    zoo_watcher.close()

This file allows us to test out the different capabilities of the Zookeeper Watcher. Now, save this file as ``example_zw.py`` or use the one located at ``utils/examples/example_zw.py`` and then in a new terminal use the ``file_pusher.py`` to push a sample settings file like shown below.

**settings.txt**

::

    My configuration string here. Typically YAML or JSON

Push the configuration into Zookeeper

::

    $ python file_pusher.py -f settings.txt -i myconfig -p /tmp/ -z scdev
    creaing conf node

Run the file watcher.

::

    $ python example_zw.py -z scdev -f /tmp/myconfig --poll
    Valid File? True
    Contents: My configuration string here. Typically YAML or JSON

You can see it already grabbed the contents of your file. Lets now change the file while the process is still running. Update your **settings.txt** file.

::

    NEW My configuration string here. Typically YAML or JSON

Now push it up with the same above command. In your watcher window, you will see the text output flip over to the following.

::

    Valid File? True
    Contents: My configuration string here. Typically YAML or JSON

    Valid File? True
    Contents: NEW My configuration string here. Typically YAML or JSON


Now, lets try it in event mode. Stop your initial process and restart it with these new parameters

::

    $ python example_zw.py -z scdev -f /tmp/myconfig --event
    Your file contents: NEW My configuration string here. Typically YAML or JSON

    The valid state is now True
    Use a keyboard interrupt to shut down the process.

Notice both the valid state handler and the file string were triggered once and only once. Lets now update that configuration file one more time.

**settings.txt**

::

    EVENT TRIGGER My configuration string here. Typically YAML or JSON

When you push that up via the same file pusher command prior, an event will fire in your watcher window only once.

::

    Your file contents: EVENT TRIGGER My configuration string here. Typically YAML or JSON

Lastly, lets change our example to be `pointer` based, meaning that the initial file we push up should have a single line inside it that points to another location in Zookeeper. Stop your initial Zookeeper Watcher process and update the settings file.

**settings.txt**

::

    /tmp/myconfig

We should put this somewhere else within zookeeper, as it stores a pointer to the file we actually care about. Push this into a new pointers folder

::

    $ python file_pusher.py -f settings.txt -i pointer1 -p /tmp_pointers/ -z scdev

Now we have a pointer and the old config file. Let us make another config file for fun.

**settings2.txt**

::

    this is another config

Push it up.

::

    $ python file_pusher.py -f settings2.txt -i myconfig2 -p /tmp/ -z scdev
    creaing conf node

So now we have two configuration files located at ``/tmp/``, and one pointer file located in ``/tmp_pointers/``. Now lets run our watcher in pointer mode, with the file path specifying the pointer path instead.

::

    $ python example_zw.py -z scdev -f /tmp_pointers/pointer1 --event -p
    Your file contents: EVENT TRIGGER My configuration string here. Typically YAML or JSON

    The valid state is now True

Neat! It shows the actual configuration we care about, instead of the path pointer.

.. warning:: If you receive ``The valid state is now False, An error was thrown: Invalid pointer path`` error, you most likely have a newline in your pointer file! This is very easy to eliminate with code, but can be hard to detect in typical text editors. **You should have one line only in the pointer file**

Now that we have the configuration we care about, with the watcher process still running we will change the configuration `pointer`, not the configuration file.

**settings.txt**

::

    /tmp/myconfig2

Lets push it up, and watch our configuration change.

::

    $ python file_pusher.py -f settings.txt -i pointer1 -p /tmp_pointers/ -z scdev

The change

::

    Your file contents: this is another config

We also have the ability to update that configuration too.

**settings2.txt**

::

    this is another config I ADDED NEW STUFF

Push it up

::

    $ python file_pusher.py -f settings2.txt -i mfig2 -p /tmp/ -z scdev

The change in the watcher process

::

    Your file contents: this is another config I ADDED NEW STUFF

The example application received the updated changes of the file it is pointed at!

What we have here is the ability to have a 'bank' of configuration files within a centrally located place (Zookeeper). This allows us to only care where our 'pointer' sits, and be directed to the appropriate real configuration file. We will get the changes when the pointed at file is updated, or we need to point to a different file (updates to the pointer file).

Hopefully this example has shown the power behind the Zookeeper Watcher utility class. It allows your application to receive and act on updates to files stored within Zookeeper in an easy to use manner, without the overhead and complexity of setting up individual file notifications and management of them.


