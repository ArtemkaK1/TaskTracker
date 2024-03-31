from concurrent import futures
import grpc
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from Protos.task_service_pb2_grpc import *
from Protos.task_service_pb2 import *

# Database configuration
DATABASE_URL = "postgresql://postgres:12345@tasks_db/tasks_data"

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks_data"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    author_id = Column(String, nullable=False)
    completed = Column(Boolean)


class TaskService(TaskServiceServicer):

    def __init__(self):
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def CreateTask(self, request, context):
        new_task = Task(
            title=request.title,
            description=request.description,
            author_id=request.author_id,
            completed=False
        )
        self.session.add(new_task)
        self.session.commit()
        self.session.refresh(new_task)
        print(new_task.title, type(new_task.author_id))
        return new_task

    def UpdateTask(self, request, context):
        task = self.session.query(Task).get(request.task.id)
        if not task:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        # Update task attributes based on request
        for field, value in request.task.__dict__.items():
            if field != "id":
                setattr(task, field, value)
        self.session.commit()
        return task

    def DeleteTask(self, request, context):
        task = self.session.query(Task).get(request.id)
        if not task:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        self.session.delete(task)
        self.session.commit()
        return Empty()

    def GetTask(self, request, context):
        task = self.session.query(Task).get(request.id)
        if not task:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        return task

    def ListTasks(self, request, context):
        query = self.session.query(Task)
        if request.page and request.per_page:
            query = query.limit(request.per_page).offset((request.page - 1) * request.per_page)
        tasks = query.all()
        return ListTasksResponse(tasks=tasks)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_TaskServiceServicer_to_server(TaskService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()