import urllib
import datetime

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from celery.backends.base import BaseDictBackend
from ghettoq.backends.base import BaseBackend
from ghettoq.taproot import MultiBackend

from alchemy_models import Task, TaskSet, Queue, Message

server = '<sql server host>'
database = '<your db>'
userid = '<your user>'
password = '<your password>'
port = 1433
raw_cs = "DRIVER={FreeTDS};SERVER=%s;PORT=%d;DATABASE=%s;UID=%s;PWD=%s;CHARSET=UTF8;TDS_VERSION=8.0;TEXTSIZE=10000" % (server, port, database, userid, password)
connection_string = "mssql:///?odbc_connect=%s" % urllib.quote_plus(raw_cs)
#connection_string = 'sqlite:////mnt/winctmp/celery.db'
#connection_string = 'sqlite:///celery.db'
engine = sqlalchemy.create_engine(connection_string, echo=True)
Session = sessionmaker(bind=engine)

class CeleryBackend(BaseDictBackend):
    """The database backends. Using Django models to store task metadata."""

    def _store_result(self, task_id, result, status, traceback=None):
        """Store return value and statu of an executed task."""
        session = Session()
        try:
            tasks = session.query(Task).filter(Task.task_id == task_id).all()
            if not tasks:
                raise RuntimeError('Task with task_id: %s not found' % task_id)
            tasks[0].result = result
            tasks[0].status = status
            tasks[0].traceback = traceback
            session.commit()
        finally:
            session.close()
        return result

    def _save_taskset(self, taskset_id, result):
        """Store the result of an executed taskset."""
        taskset = TaskSet(taskset_id, result)
        session = Session()
        try:
            session.add(taskset)
            session.commit()
        finally:
            session.close()
        return result

    def _get_task_meta_for(self, task_id):
        """Get task metadata for a task by id."""
        session = Session()
        try:
            task = None
            for task in session.query(Task).filter(Task.task_id == task_id):
                break
            if not task:
                task = Task(task_id)
                session.add(task)
                session.commit()
            if task:
                return task.to_dict()
        finally:
            session.close()

    def _restore_taskset(self, taskset_id):
        """Get taskset metadata for a taskset by id."""
        session = Session()
        try:
            for taskset in session.query(TaskSet).filter(TaskSet.task_id == task_id):
                return taskset.to_dict()
        finally:
            session.close()

    def cleanup(self):
        """Delete expired metadata."""
        from celery import conf
        expires = conf.TASK_RESULT_EXPIRES
        session = Session()
        try:
            for task in session.query(Task).filter(Task.date_done < (datetime.now() - expires)):
                session.delete(task)
            for taskset in session.query(TaskSet).filter(TaskSet.date_done < (datetime.now() - expires)):
                session.delete(taskset)
            session.commit()
        finally:
            session.close()

class CarrotBackend(MultiBackend):
    type = "alchemy_backend.GhettoqBackend"

class GhettoqBackend(BaseBackend):

    def __init__(self, *args, **kwargs):
        super(GhettoqBackend, self).__init__(*args, **kwargs)

    def establish_connection(self):
        pass

    def put(self, queue_name, payload):
        session = Session()
        try:
            # Look up queue to see if it is already there.
            queues = session.query(Queue).filter(Queue.name == queue_name).all()
            if not queues:
                queue = Queue(queue_name)
                #session.add(queue)
            else:
                queue = queues[0]
            msg = Message(payload, queue)
            session.add(msg)
            session.commit()
        finally:
            session.close()

    def get(self, queue_name):
        session = Session()
        try:
            queues = session.query(Queue).filter(Queue.name == queue_name).all()
            if queues:
                msgs = session \
                        .query(Message) \
                        .filter(Message.queue_id == queues[0].id) \
                        .filter(Message.visible != 0) \
                        .order_by(Message.sent_at) \
                        .order_by(Message.id) \
                        .limit(1) \
                        .all()
                if msgs:
                    msg = msgs[0]
                    msg.visible = False
                    session.commit()
                    return msg.payload
        finally:
            session.close()

    def purge(self, queue):
        session = Session()
        try:
            queues = session.query(Queue).filter(Queue.name == queue_name).all()
            if queues:
                cnt = session \
                        .query(Message) \
                        .filter(queue_id == queues[0].id) \
                        .delete(synchronize_session=False)
                session.commit()
                return cnt
        finally:
            session.close()

    #def purge(self, queue):
    #    session = Session()
    #    cnt = session.query(Message).filter(Message.visible == 0).delete(synchronize_session=False)
    #    session.commit()
    #    return cnt
