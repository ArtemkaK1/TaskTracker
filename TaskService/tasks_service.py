from concurrent import futures
import grpc
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from Protos.task_service_pb2_grpc import *
from Protos.task_service_pb2 import *

from tasks_model import Task, Base

# Database configuration
DATABASE_URL = "postgresql://postgres:12345@tasks_db/tasks_db"
engine = create_engine(DATABASE_URL)


class TaskService(TaskServiceServicer):

    def __init__(self):
        TaskSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session = TaskSession()

    def CreateTask(self, request, context):
        print(type(request.author_id))
        new_task = Task(
            title=request.title,
            description=request.description,
            author_id=request.author_id,
            completed=False
        )
        self.session.add(new_task)
        self.session.commit()
        self.session.refresh(new_task)
        return TaskResponse(status=200, task=new_task.to_proto())

    def UpdateTask(self, request, context):
        task = self.session.query(Task).get(request.id)
        if not task:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        if task.author_id != request.author_id:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'You cannot edit this task')

        task.title = request.title or task.title
        task.description = request.description or task.description
        task.completed = request.completed
        self.session.commit()
        return TaskResponse(status=200, task=task.to_proto())

    def DeleteTask(self, request, context):
        task = self.session.query(Task).get(request.id)
        if not task:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        if task.author_id != request.author_id:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'You cannot delete this task')
        self.session.delete(task)
        self.session.commit()
        return TaskResponse(status=200, task=task.to_proto())

    def GetTask(self, request, context):
        task = self.session.query(Task).get(request.id)
        if not task:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        return TaskResponse(status=200, task=task.to_proto())

    def ListTasks(self, request, context):
        query = self.session.query(Task)
        total_count = query.count()
        query = query.limit(request.per_page).offset((request.page - 1) * request.per_page)
        tasks = query.all()
        return ListTasksResponse(status=200, tasks=[task.to_proto() for task in tasks], total_count=total_count)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_TaskServiceServicer_to_server(TaskService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    serve()
