import datetime

from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, \
        PickleType, Sequence, Boolean, CheckConstraint, ForeignKey
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base
from celery import states

ModelBase = declarative_base()

class Task(ModelBase):
    """Task result/status."""
    __tablename__ = 'celery_taskmeta'

    id        = Column("id", Integer, Sequence('task_id_sequence'), primary_key=True)
    task_id   = Column('task_id', String(255), primary_key = True)
    status    = Column('status',
                       String(50),
                       CheckConstraint("status in (%s)"
                                       % ', '.join(["'%s'" % state
                                                    for state in states.ALL_STATES])),
                       default = states.PENDING)
    result    = Column('result', PickleType, nullable=True)
    date_done = Column('date_done', DateTime, onupdate = datetime.datetime.now, nullable=True)
    traceback = Column('traceback', Text, nullable=True)

    def __init__(self, task_id):
        self.task_id = task_id
        #self.result = ''

    def __str__(self):
        return "<Task(%s, %s, %s, %s)>" % (self.task_id, self.result, self.status, self.traceback)

    def to_dict(self):
        return {"task_id"   : self.task_id,
                "status"    : self.status,
                "result"    : self.result,
                "date_done" : self.date_done,
                "traceback" : self.traceback}

    def __unicode__(self):
        return u"<Task: %s successful: %s>" % (self.task_id, self.status)

class TaskSet(ModelBase):
    """TaskSet result"""
    __tablename__ = 'celery_tasksetmeta'

    id         = Column("id", Integer, Sequence('taskset_id_sequence'), primary_key=True)
    taskset_id = Column('taskset_id', String(255), unique = True)
    result     = Column('result', PickleType, nullable=True)
    date_done = Column('date_done', DateTime, onupdate = datetime.datetime.now, nullable=True)

    def __init__(self, task_id):
        self.task_id = task_id

    def __str__(self):
        return "<TaskSet(%s, %s)>" % (self.task_id, self.result)

    def to_dict(self):
        return {"taskset_id" : self.taskset_id,
                "result"     : self.result,
                "date_done"  : self.date_done}

    def __unicode__(self):
        return u"<TaskSet: %s>" % (self.taskset_id)

class Queue(ModelBase):
    __tablename__ = 'ghettoq_queue'

    id       = Column("id", Integer, Sequence('queue_id_sequence'), primary_key=True)
    name     = Column("name", String(200), unique=True)
    messages = relation("Message", backref='queue', lazy='noload')

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "<Queue(%s)>" % (self.name)

class Message(ModelBase):
    __tablename__ = 'ghettoq_message'

    id       = Column("id", Integer, Sequence('message_id_sequence'), primary_key=True)
    visible  = Column("visible", Boolean, default=True, index=True)
    sent_at  = Column('timestamp', DateTime, nullable=True, index=True,
                      onupdate = datetime.datetime.now)
    payload  = Column("payload", Text, nullable=False)
    queue_id = Column('queue_id', Integer, ForeignKey('ghettoq_queue.id', name='FK_qhettoq_message_queue'))

    def __init__(self, payload, queue):
        self.payload  = payload
        self.queue = queue

    def __str__(self):
        return "<Message(%s, %s, %s, %s)>" % (self.visible, self.sent_at, self.payload, self.queue_id)
