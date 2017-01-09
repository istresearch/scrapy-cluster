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