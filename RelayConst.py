# -*- coding:utf-8 -*-
"""
Created on 2017-2-28 
@author:  Kyrie Liu  
@description:  Global variable
"""
import Const


# DATABASE TABLE KEYS
Const.DB_TABLE_KEYS            = ['Date DATE',
                                   'PC VARCHAR(256)',
                                   'Chipset VARCHAR(256)',
                                   'Serial VARCHAR(256)',
                                   'IMEI VARCHAR(256)',
                                   'AdbLost INTEGER',
                                   'AdbRecovery INTEGER',
                                   'Build TEXT']
# DATABASE TABLE NAME
Const.DB_TABLE_NAME            = 'pm_recoveryadbdata'

# DATABASE CONFIG
Const.HOST                     = 'xx.xx.xx.xx'
Const.USER                     = 'xxx_ccn'
Const.PASSWD                   = 'xxx_ccn'
Const.DB_NAME                  = 'test'
Const.PORT                     = 3306
Const.GETPROP_PRODUCT          = 'getprop ro.build.product'

# MSG
Const.RELAY_DISCONNT_MSG       = 0
Const.RELAY_CONNECT_MSG        = 1
Const.RELAY_DISCONNT_MSG_SEC   = 2
Const.RELAY_CONNECT_MSG_SEC    = 3
Const.RELAY_GET_STATE_MSG      = 4
Const.RELAY_SET_STATE_MSG      = 5
