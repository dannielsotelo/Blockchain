import addressing
from protobuf.task_pb2 import *
from protobuf.project_node_pb2 import *
import base64
import requests
import json

def getProjectNode(state,project_name):
    ''' Given a project name get a project node. '''

    # make address of project metanode
    project_node_address = addressing.make_project_node_address(project_name)
    project_node_container = ProjectNodeContainer()
    data = getData(state,project_node_address)
    project_node_container.ParseFromString(data)  # decode data and store in container

    for project_node in project_node_container.entries:  # find project with correct name
        if project_node.project_name == project_name:
            return project_node
    return None

def getTask(state,project_name,task_name):
    ''' Given a project name and task name get a task node. '''

    # make address of task node
    task_address = addressing.make_task_address(project_name,task_name)
    task_container = TaskContainer()
    data = getData(state,task_address)
    task_container.ParseFromString(data)  # decode data and store in container

    for task in task_container.entries:  # find task with correct name
        if task.task_name == task_name:
            return task
    return None


def getData(state, address):
    ''' Gets the data from a provided address.
        State has two fields address and data.  We can create the
        address using functions in addressing.py.  The data field
        is encoded with base64 encoding.
    '''

    for location in state:
        print(location)
        print(address)
        if location['address'] == address:
            encoded_data = location['data']
            return base64.b64decode(encoded_data)
    return None

args = sys.argv[1:]
if not len(args) == 1:  # make sure correct number of arguments are present
    print("\nIncorrect number of arguments for desired command.\n")
    quit()
# queries state
resp = requests.get("http://10.138.0.10:8008/state")
state = json.loads(resp.text)['data']
project_name = args[0]
# gets project node from state
project_node = getProjectNode(state, project_name)
print('+++++++++++++++++++++Project:' + project_name + '+++++++++++++++++++++')
print("<<<<<<<<<<<Public Keys:>>>>>>>>>>>>")
# print all authorized public keys
for public_key in project_node.public_keys:
    print(public_key)
print("<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>")
for task_name in project_node.task_names:
    task = getTask(state, project_name, task_name)
    print("------------Task------------")
    print("Task_name: " + task.task_name)
    print('Description: ' + task.description)
    print('Progress: ' + str(task.progress))
    print('---------------------------')
print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
