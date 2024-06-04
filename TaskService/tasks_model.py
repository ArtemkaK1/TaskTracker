from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase
import Protos.task_service_pb2 as task_service_pb2


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks_data"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    author_id = Column(Integer, nullable=False)
    completed = Column(Boolean)

    def to_proto(self):
        return task_service_pb2.Task(
            id=self.id,
            title=self.title,
            description=self.description if self.description else "",
            author_id=self.author_id,
            completed=self.completed
        )
