import importlib


class SettingsWrapper(object):
    '''
    Wrapper for loading settings files and merging them with overrides
    '''

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

    def load(self, local='localsettings.py', default='settings.py'):
        '''
        Load the settings dict

        @param local: The local settings filename to use
        @param default: The default settings module to read
        @return: A dict of the loaded settings
        '''
        self._load_defaults(default)
        self._load_custom(local)

        return self.settings()

    def settings(self):
        '''
        Returns the current settings dictionary
        '''
        return self.my_settings

    def _load_defaults(self, default='settings.py'):
        '''
        Load the default settings
        '''
        if default[-3:] == '.py':
            default = default[:-3]

        self.my_settings = {}
        try:
            settings = importlib.import_module(default)
            self.my_settings = self._convert_to_dict(settings)
        except ImportError:
            print "No default settings found"

    def _load_custom(self, settings_name='localsettings.py'):
        '''
        Load the user defined settings, overriding the defaults

        '''
        if settings_name[-3:] == '.py':
            settings_name = settings_name[:-3]

        new_settings = {}
        try:
            settings = importlib.import_module(settings_name)
            new_settings = self._convert_to_dict(settings)
        except ImportError:
            print "No override settings found"

        for key in new_settings:
            if key in self.my_settings:
                item = new_settings[key]
                if isinstance(item, dict) and \
                        isinstance(self.my_settings[key], dict):
                    for key2 in item:
                        self.my_settings[key][key2] = item[key2]
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
