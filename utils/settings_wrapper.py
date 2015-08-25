import importlib
from log_factory import LogFactory

class SettingsWrapper(object):
    '''
    Wrapper for loading settings files and merging them with overrides
    '''

    default_settings = "default_settings"
    my_settings = {}
    ignore = [
        '__builtins__',
        '__file__',
        '__package__',
        '__doc__',
        '__name__',
    ]

    def _init__(self):
        pass

    def setup(self, **kwargs):
        '''
        Sets up the SettingsWrapper
        '''
        self.logger = LogFactory.get_instance(**kwargs)

    def load_defaults(self):
        '''
        Load the default settings
        '''
        self.logger.debug("Loading default settings")
        settings = importlib.import_module(self.default_settings)
        self.my_settings = self._convert_to_dict(settings)

    def load_custom(self, settings_name='settings.py'):
        '''
        Load the user defined settings, overriding the defaults

        @param settings_name: The settings file to use
        '''
        if settings_name[-3:] == '.py':
            settings_name = settings_name[:-3]

        self.logger.debug("Loading settings {name}".format(name=settings_name))
        settings = importlib.import_module(settings_name)
        new_settings = self._convert_to_dict(settings)

        for key in new_settings:
            self.logger.debug('Override setting {k} : {v}'.format(
                    k=key,v=new_settings[key]))
            if key in self.my_settings:
                item = new_settings[key]
                if isinstance(item, dict):
                    for key in item:
                        self.my_settings[key] = item[key]
                else:
                    self.my_settings[key] = item
            else:
                self.my_settings[key] = new_settings[key]

    def _convert_to_dict(self, setting):
        '''
        Converts a settings file into a dictionary, ignoring python defaults

        @param setting: A loaded setting module
        '''
        the_dict = {}
        set = dir(setting)
        for key in set:
            if key in self.ignore:
                continue
            value = getattr(setting, key)
            the_dict[key] = value

        return the_dict
