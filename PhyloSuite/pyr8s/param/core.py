#-----------------------------------------------------------------------------
# Pyr8s - Divergence Time Estimation
# Copyright (C) 2021  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------


"""
Parameter classes for use by core.Analysis class.
Parameter declarations and defaults are loaded from a json file.

Interactive python console example:
(assume ParamList param)

Browse available categories:
>>> param.keys()

Browse category 'general':
>>> param.general.keys()

Get the value of a specific field:
>>> f = param.general.scalar

Set the value of a specific field:
>>> param.general.scalar = True

Access field documentation:
>>> param.general['scalar'].doc
"""

# Default dict is ordered in Python3.7+, but we use Python3.6
from collections import OrderedDict
import json

class ParamField():
    """Information about this parameter"""

    def __repr__(self):
        return '(' + str(self.label) + ': ' + str(self.value) + ')'

    def __dir__(self):
        return list(vars(self))

    def __init__(self, dictionary):
        self.label = dictionary['label']
        self.doc = dictionary['doc']
        self.type = dictionary['type']
        self.default = dictionary['default']

        if 'data' in dictionary.keys():
            self.data = dictionary['data']
        else:
            self.data = {}

        self.value = dictionary['default']

class ParamCategory(OrderedDict):
    """Dictionary of fields belonging to this category."""

    def __getattr__(self, name):
        try:
            return self[name].value
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self.keys():
            try:
                self[name].value = value
            except KeyError:
                raise AttributeError(name)
        else:
            object.__setattr__(self, name, value)

    def __repr__(self):
        if self.keys():
            m = max(map(len, list(self.keys()))) + 1
            return '\n'.join([k.rjust(m) + ': ' + repr(v)
                              for k, v in sorted(self.items())])
        else:
            return self.__class__.__name__ + "()"

    def __dir__(self):
        return list(self.keys())

    def __init__(self, dictionary):
        if dictionary is None:
            return
        self.label = dictionary['label']
        for k in dictionary['fields'].keys():
            self[k] = ParamField(dictionary['fields'][k])

    def __reduce__(self):
        state = super().__reduce__()
        newstate = (state[0],
                    (None, ),
                    None,
                    None,
                    state[4])
        return newstate

    def as_dictionary(self):
        """Return key/value pairs of category parameters"""
        dictionary = {}
        for param in self.keys():
            dictionary[param] = self[param].value
        return dictionary


class ParamList(OrderedDict):
    """Dictionary of all categories."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __repr__(self):
        if self.keys():
            m = max(map(len, list(self.keys()))) + 1
            return '\n'.join([k.rjust(m) + ': ' + repr(v)
                              for k, v in sorted(self.items())])
        else:
            return self.__class__.__name__ + "()"

    def __dir__(self):
        return list(self.keys())

    def __init__(self, dictionary=None, json_data=None):
        super().__init__()
        if json_data is not None:
            dictionary = json.load(json_data, object_pairs_hook=OrderedDict)
        #dictionary = json.load(data)
        if dictionary is None:
            return
        for k in dictionary.keys():
            self[k] = ParamCategory(dictionary[k])

    def __reduce__(self):
        state = super().__reduce__()
        newstate = (state[0],
                    (None, ),
                    None,
                    None,
                    state[4])
        return newstate

    def as_dictionary(self):
        """Return key/value pairs for all categories"""
        dictionary = {}
        for category in self.keys():
            category_dictionary = self[category].as_dictionary()
            for param in category_dictionary.keys():
                if dictionary.get(param) is not None:
                    raise RuntimeError("Duplicate key: "+param)
                else:
                    dictionary[param] = category_dictionary[param]
        return dictionary
