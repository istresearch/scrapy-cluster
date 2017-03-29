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