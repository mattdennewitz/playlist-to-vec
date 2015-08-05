from __future__ import absolute_import

from celery import Celery

from . import celeryconfig


app = Celery('artistrecs')
app.config_from_object(celeryconfig)
app.autodiscover_tasks(['artistrecs'], force=True)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
