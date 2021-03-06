# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os

from flask_appbuilder.security.manager import AUTH_DB, AUTH_LDAP

def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = 'The environment variable {} was missing, abort...'\
                        .format(var_name)
            raise EnvironmentError(error_msg)

APP_NAME = get_env_variable('SUPERSET_APP_NAME')
POSTGRES_USER = get_env_variable('POSTGRES_USER')
POSTGRES_PASSWORD = get_env_variable('POSTGRES_PASSWORD')
POSTGRES_HOST = get_env_variable('POSTGRES_HOST')
POSTGRES_PORT = get_env_variable('POSTGRES_PORT')
POSTGRES_DB = get_env_variable('POSTGRES_DB')

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'postgresql://%s:%s@%s:%s/%s' % (POSTGRES_USER,
                                                           POSTGRES_PASSWORD,
                                                           POSTGRES_HOST,
                                                           POSTGRES_PORT,
                                                           POSTGRES_DB)

REDIS_HOST = get_env_variable('REDIS_HOST')
REDIS_PORT = get_env_variable('REDIS_PORT')

#Authentication Stuff

if get_env_variable('SUPERSET_AUTH_TYPE') == 'AUTH_LDAP':
    AUTH_TYPE = AUTH_LDAP
elif get_env_variable('SUPERSET_AUTH_TYPE') == 'AUTH_DB':
    AUTH_TYPE = AUTH_DB
else:
    AUTH_TYPE = AUTH_DB

AUTH_LDAP_SERVER = get_env_variable('SUPERSET_LDAP_SERVER')
AUTH_LDAP_ALLOW_SELF_SIGNED = get_env_variable('SUPERSET_LDAP_ALLOW_SELF_SIGNED')
AUTH_LDAP_SEARCH = get_env_variable('SUPERSET_AUTH_LDAP_SEARCH')
AUTH_LDAP_BIND_USER = get_env_variable('SUPERSET_AUTH_LDAP_BIND_USER')
AUTH_LDAP_BIND_PASSWORD = get_env_variable('SUPERSET_AUTH_LDAP_BIND_PASSWORD')
AUTH_USER_REGISTRATION = get_env_variable('SUPERSET_AUTH_USER_REGISTRATION')
AUTH_USER_REGISTRATION_ROLE = get_env_variable('SUPERSET_AUTH_USER_REGISTRATION_ROLE')
AUTH_LDAP_UID_FIELD = get_env_variable('SUPERSET_AUTH_LDAP_UID_FIELD')


class CeleryConfig(object):
    BROKER_URL = 'redis://%s:%s/0' % (REDIS_HOST, REDIS_PORT)
    CELERY_IMPORTS = ('superset.sql_lab', )
    CELERY_RESULT_BACKEND = 'redis://%s:%s/1' % (REDIS_HOST, REDIS_PORT)
    CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '10/s'}}
    CELERY_TASK_PROTOCOL = 1


CELERY_CONFIG = CeleryConfig
