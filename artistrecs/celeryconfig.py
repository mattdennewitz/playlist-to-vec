from __future__ import absolute_import, unicode_literals
import os


#
# Worker configuration
#

DEFAULT_URL = 'redis://localhost:6379/0'

BROKER_URL = os.environ.get('ARTISTRECS_BROKER_URL', DEFAULT_URL)
CELERY_RESULT_BACKEND = os.environ.get('ARTISTRECS_RESULT_BACKEND',
                                       DEFAULT_URL)
