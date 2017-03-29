Argparse Helper
===============

The Argparse Helper class is a small utility designed to help developers create cleaner and more maintainable ``--help`` messages when using `Argparse sub-commands <https://docs.python.org/2/library/argparse.html#sub-commands>`_.

The default behavior when passing a ``-h`` or ``--help`` flag to your script prints out only minimal information about the subcommands. This utility class allows you to print out more information about how to run each of those subcommands from your main parser invocation.

The ArgparseHelper class does not have any direct method calls. Instead, the class is passed as a parameter when setting up your argument parser.

Usage
-----

Using the ArgparseHelper class to display help information requires modification to the following two lines when setting up the parser.

::

    import argparse
    from scutils.argparse_helper import ArgparseHelper

    parser = argparse.ArgumentParser(
        description='my_script.py: Used for processing widgets', add_help=False)
    parser.add_argument('-h', '--help', action=ArgparseHelper,
                        help='show this help message and exit')

After the imports, we state that we do not want to use the default Argparse help functionality by specifying ``add_help=False``. Next, we our own custom help message and pass the ArgparseHelper class for the ``action`` parameter.

You are now free to add subcommands with whatever parameters you like, and when users run ``my_script.py -h`` they will see the full list of acceptable ways to run your program.

Example
-------

Put the following code into ``example_ah.py``, or use the file located at ``utils/examples/example_ah.py``

::

    import argparse
    from scutils.argparse_helper import ArgparseHelper

    parser = argparse.ArgumentParser(
        description='example_ah.py: Prints various family members', add_help=False)
    parser.add_argument('-h', '--help', action=ArgparseHelper,
                        help='show this help message and exit')
    # use the default argparse setup, comment out the lines above
    #parser = argparse.ArgumentParser(
    #    description='example_ah.py: Prints various family members')

    subparsers = parser.add_subparsers(help='commands', dest='command')

    # args here are applied to all sub commands using the `parents` parameter
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('-n', '--name', action='store', required=True,
                            help="The name of the person running the program")

    # subcommand 1, requires name of brother
    bro_parser = subparsers.add_parser('bro', help='Prints only the brother\'s name',
                                       parents=[base_parser])
    bro_parser.add_argument('-b', '--brother', action='store', required=True,
                             help="The brother's name")

    # subcommand 2, requires name of sister and optionally mom
    fam_parser = subparsers.add_parser('fam', help='Prints mom and sister\'s name',
                                       parents=[base_parser])
    fam_parser.add_argument('-s', '--sister', action='store', required=True,
                             help="The sister's name")
    fam_parser.add_argument('-m', '--mom', action='store', required=False,
                             default='Mom', help="The sister's name")

    args = vars(parser.parse_args())

    if args['command'] == 'bro':
        print "Your brother's name is " + args['brother']
    elif args['command'] == 'fam':
        print "Your sister's name is " + args['sister'] + " and you call your "\
            "Mother '" + args['mom'] + "'"

Running ``-h`` from the base command prints out nicely formatted statements for all your subcommands.

::

    $ python example_ah.py -h
    usage: example_ah.py [-h] {bro,fam} ...

    example_ah.py: Prints various family members

    positional arguments:
      {bro,fam}   commands
        bro       Prints only the brother's name
        fam       Prints mom and sister's name

    optional arguments:
      -h, --help  show this help message and exit

    Command 'bro'
    usage: example_ah.py bro [-h] -n NAME -b BROTHER

    Command 'fam'
    usage: example_ah.py fam [-h] -n NAME -s SISTER [-m MOM]

If you comment out the first two lines, and replace them with the simpler commented out line below it, you get the default Argparse behavior like shown below.

::

    $ python example_ah.py -h
    usage: example_ah.py [-h] {bro,fam} ...

    example_ah.py: Prints various family members

    positional arguments:
      {bro,fam}   commands
        bro       Prints only the brother's name
        fam       Prints mom and sister's name

    optional arguments:
      -h, --help  show this help message and exit

You can see that this does not actually display to the user how to run your script sub-commands, and they have to type another ``python example_ah.py bro -h`` to see the arguments they need. Of course, you can always create your own ``description`` string for your default help message, but now you have to maintain the arguments to your commands in two places (the description string and in the code) instead of one.

The ArgparseHelper class allows you to keep your parameter documentation in one place, while allowing users running your script to see more detail about each of your subcommands.