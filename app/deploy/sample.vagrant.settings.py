#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Goal: store confidential settings

Note: this file is *not* used for deployment.
"""

# (!) Never run in production with debug mode enabled
DEBUG = False
DEBUG_TB_ENABLED = False

# This is generated automatically during deployment with fabric
SECRET_KEY = 'change_me'

DB_USER = 'olass'
DB_PASS = 'insecurepassword'
DB_HOST = 'localhost'
DB_NAME = 'olass'

# Override the SSL cert config if the defaults in config.py are not suitable
SERVER_SSL_KEY_FILE = 'ssl/server.key'
SERVER_SSL_CRT_FILE = 'ssl/server.crt'

APP_VERSION = '0.0.1'
