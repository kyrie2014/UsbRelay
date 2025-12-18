# -*- coding:utf-8 -*-
"""
Created on 2017-2-28 
@author:  Kyrie Liu  
@description:  Global variable
"""

import sys


class Const(object):

    class ConstError(TypeError):
        pass
    
    def __setattr__(self, key, value):
        if key in self.__dict__:
            raise self.ConstError("Not changed the value of const.%s" % key)
        else:
            self.__dict__[key] = value
            
    def __getattr__(self, key):
        return self.key if key in self.__dict__ else None

sys.modules[__name__] = Const()
