import argparse
from scutils.log_factory import LogFactory
parser = argparse.ArgumentParser(description='Example logger.')
parser.add_argument('-ll', '--log-level', action='store', required=False,
                    help="The log level", default='INFO',
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
parser.add_argument('-lf', '--log-file', action='store_const',
                    required=False, const=False, default=True,
                    help='Log the output to the file. Otherwise logs to stdout')
parser.add_argument('-lj', '--log-json', action='store_const',
                    required=False, const=True, default=False,
                    help="Log the data in JSON format")
parser.add_argument('-ie', '--include-extra', action='store_const', const=True,
                        default=False, help="Print the 'extra' dict if not logging"
                        " to json")
args = vars(parser.parse_args())
logger = LogFactory.get_instance(level=args['log_level'], stdout=args['log_file'],
                    json=args['log_json'], include_extra=args['include_extra'])

my_var = 1

def the_callback(log_message, log_extras):
    global my_var
    my_var += 5

def the_callback_2(log_message, log_extras):
    global my_var
    my_var *= 2

logger.register_callback('DEBUG', the_callback)
logger.register_callback('WARN', the_callback_2, {'key':"value"})

logger.debug("debug output 1")
logger.warn("warn output", extra={"key":"value", "key2":"value2"})
logger.warn("warn output 2")
logger.debug("debug output 2")
logger.critical("critical fault, closing")
logger.debug("debug output 3")
sum = 2 + 2
logger.info("Info output closing.", extra={"sum":sum})
logger.error("Final var value", extra={"value": my_var})