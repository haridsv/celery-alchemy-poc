import datetime

from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, \
        PickleType, Sequence, Boolean, CheckConstraint, ForeignKey, SmallInteger
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from celery import states

metadata = MetaData()
ModelBase = declarative_base(metadata=metadata)

class Task(ModelBase):
    """Task result/status."""
    __tablename__ = 'celery_taskmeta'
    __table_args__ = {"sqlite_autoincrement": True}

    id         = Column(Integer, Sequence('task_id_sequence'), primary_key=True,
                        autoincrement=True)
    task_id    = Column(String(255))
    status     = Column(String(50),
                        CheckConstraint("status in (%s)"
                                        % ', '.join(["'%s'" % state
                                                     for state in states.ALL_STATES])),
                        default = states.PENDING)
    result     = Column(PickleType, nullable=True)
    date_began = Column(DateTime, nullable=True)
    date_done  = Column(DateTime, onupdate = datetime.datetime.now, nullable=True)
    traceback  = Column(Text, nullable=True)

    def __init__(self, task_id):
        self.task_id = task_id

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
    __table_args__ = {"sqlite_autoincrement": True}

    id         = Column(Integer, Sequence('taskset_id_sequence'), primary_key=True,
                        autoincrement=True)
    taskset_id = Column(String(255))
    result     = Column(PickleType, nullable=True)
    date_done  = Column(DateTime, default=datetime.datetime.now, nullable=True)

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
    __table_args__ = {"sqlite_autoincrement": True}

    id       = Column(Integer, Sequence('queue_id_sequence'), primary_key=True,
                      autoincrement=True)
    name     = Column(String(200), unique=True)
    messages = relation("Message", backref='queue', lazy='noload')

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "<Queue(%s)>" % (self.name)

class Message(ModelBase):
    __tablename__ = 'ghettoq_message'
    __table_args__ = {"sqlite_autoincrement": True}

    id       = Column(Integer, Sequence('message_id_sequence'), primary_key=True,
                      autoincrement=True)
    visible  = Column(Boolean, default=True, index=True)
    sent_at  = Column('timestamp', DateTime, nullable=True, index=True,
                      onupdate = datetime.datetime.now)
    payload  = Column(Text, nullable=False)
    queue_id = Column(SmallInteger, ForeignKey('ghettoq_queue.id', name='FK_qhettoq_message_queue'))
    version  = Column(SmallInteger, nullable=False, default=1)

    __mapper_args__ = {'version_id_col': version}

    def __init__(self, payload, queue):
        self.payload  = payload
        self.queue = queue

    def __str__(self):
        return "<Message(%s, %s, %s, %s)>" % (self.visible, self.sent_at, self.payload, self.queue_id)
