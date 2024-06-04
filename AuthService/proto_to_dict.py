from Protos.auth_service_pb2 import *


def proto_to_dict(task: Task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description if task.description else "",
        'author_id': task.author_id,
        'completed': task.completed,
    }
