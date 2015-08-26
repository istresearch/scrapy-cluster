import importlib

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

    def load(self, name='settings.py'):
        '''
        Load the settings dict

        @param name: The settings filename to use
        @return: A dict of the loaded settings
        '''
        self._load_defaults()
        self._load_custom(name)

        return self.my_settings

    def _load_defaults(self):
        '''
        Load the default settings
        '''
        settings = importlib.import_module(self.default_settings)
        self.my_settings = self._convert_to_dict(settings)

    def _load_custom(self, settings_name):
        '''
        Load the user defined settings, overriding the defaults

        '''
        if settings_name[-3:] == '.py':
            settings_name = settings_name[:-3]

        settings = importlib.import_module(settings_name)
        new_settings = self._convert_to_dict(settings)

        for key in new_settings:
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
