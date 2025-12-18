# -*- coding:utf-8 -*-
"""
Example Configuration File for USB Relay Controller

Copy this file to 'config_local.py' and modify the values according to your setup.
The config_local.py file is ignored by git to protect sensitive information.

Usage:
    cp config.example.py config_local.py
    # Then edit config_local.py with your actual credentials
"""
import Const

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# MySQL Database Host
# Examples: 'localhost', '192.168.1.100', 'db.example.com'
Const.HOST = 'localhost'

# MySQL Database User
Const.USER = 'relay_user'

# MySQL Database Password
Const.PASSWD = 'your_secure_password_here'

# MySQL Database Name
Const.DB_NAME = 'relay_test'

# MySQL Database Port (default: 3306)
Const.PORT = 3306

# =============================================================================
# DATABASE TABLE CONFIGURATION
# =============================================================================

# Database table name for storing relay recovery data
Const.DB_TABLE_NAME = 'pm_recoveryadbdata'

# Database table schema
# Note: This defines the structure of the recovery data table
Const.DB_TABLE_KEYS = [
    'ID INTEGER PRIMARY KEY AUTO_INCREMENT',
    'Date DATE',
    'PC VARCHAR(256)',
    'Chipset VARCHAR(256)',
    'Serial VARCHAR(256)',
    'IMEI VARCHAR(256)',
    'AdbLost INTEGER',
    'AdbRecovery INTEGER',
    'Build TEXT',
    'TotalRun INTEGER',
    'TotalLost INTEGER',
    'Comment TEXT',
    'RebootTimes INTEGER'
]

# =============================================================================
# ANDROID DEVICE CONFIGURATION
# =============================================================================

# ADB command to get device product name
Const.GETPROP_PRODUCT = 'getprop ro.build.product'

# =============================================================================
# RELAY CONTROL MESSAGES
# =============================================================================

# Message types for relay control (DO NOT MODIFY unless you know what you're doing)
Const.RELAY_DISCONNT_MSG = 0        # Disconnect USB by port index
Const.RELAY_CONNECT_MSG = 1         # Connect USB by port index
Const.RELAY_DISCONNT_MSG_SEC = 2    # Disconnect USB by hub value
Const.RELAY_CONNECT_MSG_SEC = 3     # Connect USB by hub value
Const.RELAY_GET_STATE_MSG = 4       # Get all port states
Const.RELAY_SET_STATE_MSG = 5       # Set port state (bind device)

# =============================================================================
# NOTES
# =============================================================================

"""
Database Setup Instructions:
----------------------------
1. Create a MySQL database:
   CREATE DATABASE relay_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

2. Create a user and grant permissions:
   CREATE USER 'relay_user'@'localhost' IDENTIFIED BY 'your_secure_password_here';
   GRANT ALL PRIVILEGES ON relay_test.* TO 'relay_user'@'localhost';
   FLUSH PRIVILEGES;

3. The table will be created automatically when you first run InitRelay.py

Hardware Setup:
--------------
1. Connect USB relay to PC via Type-B USB cable
2. Connect relay serial port to PC via Micro-B cable
3. Install relay drivers if required
4. Verify COM port in Device Manager (Windows)

Testing Configuration:
---------------------
After setting up config_local.py, test the connection:
    python -c "from DatabaseUtils import DatabaseUtils; \
               from config_local import Const; \
               db = DatabaseUtils(Const.HOST, Const.USER, Const.PASSWD, Const.DB_NAME, Const.PORT); \
               print('Database connection successful!')"
"""

