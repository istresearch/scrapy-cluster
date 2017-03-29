Settings Wrapper
================

The SettingsWrapper module provides a way to organize and override settings for you application in a consistent manner. Like many other larger frameworks that allow you to override particular settings, this class is designed to allow you to easily separate default settings from various custom configurations.

The SettingsWrapper was also created to clean up large amounts of import statements when loading different variables in from another file using the ``import`` python declaration. Instead, you point the SettingsWrapper to your settings file, and everything is loaded into a python dictionary for you.

.. class:: SettingsWrapper()

    .. method:: load(local='localsettings.py', default='settings.py')

        Loads the default settings and local override

        :param str local: The local override file to keep custom settings in
        :param str default: The core default settings file
        :returns: The settings dictionary

    .. method:: load_from_string(settings_string='', module_name='customsettings'):

        Loads your default program settings from an escaped string. Does not provide override capabilities from other strings or the ``load()`` method.

        :param str settings_string: The string containing the settings
        :param str module_name: The module name to use when loading the settings
        :returns: The loaded settings dictionary

    .. method:: settings():

        :returns: The loaded settings dictionary

.. note:: When using a local settings file, the SettingsWrapper will override lists, dictionary keys, and variables, but does not recursively override settings buried deeper than 1 layer into dictionary objects.

Usage
-----

Lets assume you have a ``settings.py`` file with the following setup:

::

    NAME='Bill'
    FAMILY = {
        'Friends': ['Joe', 'Mark'],
        'Sister': 'Kathy'
    }

You can load your settings and access them like the following

::

    >>> from scutils.settings_wrapper import SettingsWrapper
    >>> settings = SettingsWrapper()
    >>> my_settings = settings.load(default='settings.py')
    No override settings found
    >>> my_settings['NAME']
    'Bill'

Example
-------

Let's expand our use case into a working script that will accept both default settings and override settings. Use the following code as an example and save it as ``example_sw.py``, or use the one located at ``utils/examples/example_sw.py``

::

    import argparse
    from scutils.settings_wrapper import SettingsWrapper

    # set up arg parser
    parser = argparse.ArgumentParser(
        description='Example SettingsWrapper parser.\n')
    parser.add_argument('-s', '--settings', action='store', required=False,
                        help="The default settings file",
                        default="settings.py")
    parser.add_argument('-o', '--override-settings', action='store', required=False,
                        help="The override settings file",
                        default="localsettings.py")
    parser.add_argument('-v', '--variable', action='store', required=False,
                        help="The variable to print out",
                        default=None)
    args = vars(parser.parse_args())

    # load up settings
    wrapper = SettingsWrapper()
    my_settings = wrapper.load(default=args['settings'],
                               local=args['override_settings'])

    if args['variable'] is not None:
        if args['variable'] in my_settings:
            print args['variable'], '=', my_settings[args['variable']]
        else:
            print args['variable'], "not in loaded settings"
    else:
        print "Full settings:", my_settings

Now create a ``settings.py`` file containing the same settings described above. This will be our **default** settings.

::

    NAME='Bill'
    FAMILY = {
        'Friends': ['Joe', 'Mark'],
        'Sister': 'Kathy'
    }

Loading these settings is easy.

::

    $ python example_sw.py
    No override settings found
    Full settings: {'NAME': 'Bill', 'FAMILY': {'Sister': 'Kathy', 'Friends': ['Joe', 'Mark']}}

Now we want to alter our application settings for "Joe" and his family. He has the same friends as Bill, but has a different Sister and a house. This is ``joe_settings.py`` and will overlay on top of our default ``settings.py``. This override settings file only needs to contain settings we wish to add or alter from the default settings file, not the whole thing.

::

    NAME='Joe'
    FAMILY={
      'Sister':'Kim'
    }
    HOUSE=True

Using the override, we can see how things change.

::

    $ python example_sw.py -o joe_settings.py
    Full settings: {'HOUSE': True, 'NAME': 'Joe', 'FAMILY': {'Sister': 'Kim', 'Friends': ['Joe', 'Mark']}}

Notice how we were able to override a specific key in our ``FAMILY`` dictionary, without touching the other keys. If we wanted to add a final application settings file, we could add Bill's twin brother who is identical to him in every way except his name, ``ben_settings.py``.

::

    NAME='Ben'

::

    $ python example_sw.py -o ben_settings.py
    Full settings: {'NAME': 'Ben', 'FAMILY': {'Sister': 'Kathy', 'Friends': ['Joe', 'Mark']}}

If you would like to further play with this script, you can also use the ``-v`` flag to print out only a specific variable from your settings dictionary.

::

    $ python example_sw.py -o ben_settings.py -v NAME
    NAME = Ben

Hopefully by now you can see how nice it is to keep custom application settings distinct from the core default settings you may have. With just a couple of lines of code you now have a working settings manager for your application's different use cases.