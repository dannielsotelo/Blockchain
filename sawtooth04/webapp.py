import hashlib
import requests
import json
import base64

from flask import Flask, redirect, request, url_for, render_template

from protobuf.project_node_pb2 import *
from protobuf.task_pb2 import *

import transaction_factory
import addressing

app = Flask(__name__)
action = 'create_project'
fields = {"task_name" : False, "task_description" : False, "new_password" : False}
display_project_name = ''
project_node = ProjectNode()
tasks = []

@app.route('/')
def render():
    return render_template('page.html', fields=fields,action=action)

@app.route('/changeaction',methods=['POST'])
def change_action():
   switch = {
       "create_project": {"task_name": False, "task_description": False, "new_password": False},
       "create_task": {"task_name": True, "task_description": True, "new_password": False},
       "edit_task": {"task_name": True, "task_description": True, "new_password": False},
       "progress_task": {"task_name": True, "task_description": False, "new_password": False},
       "add_user": {"task_name": False, "task_description": False, "new_password": True},
   }
   global action
   action = request.form["action"]
   global fields
   fields = switch[action]
   return redirect(url_for('render'))

@app.route('/send', methods=['POST'])
def send():
    args = []
    args.append(action)
    args.append(request.form['password'])
    args.append(request.form['project_name'])
    if fields["task_name"]:
        args.append(request.form['task_name'])
    if fields["task_description"]:
        args.append(request.form['task_description'])
    if fields["new_password"]:
        args.append(request.form['new_password'])

    txn_factory = transaction_factory.Txn_Factory();
    passcode = args[1]
    priv_key = hashlib.sha256(passcode.encode('utf-8')).hexdigest()
    args[1] = transaction_factory._create_signer(priv_key)
    # run desired function
    getattr(txn_factory, args[0])(args[1:])
    return redirect(url_for('render'))


@app.route('/viewproject',methods=['POST'])
def view_project():
    project_name = request.form['project_name']
    with urllib.request.urlopen("http://<IPaddr_of_backend>:8008/state") as url:
        state = json.loads(url.read().decode())['data']
    global project_node
    global tasks
    tasks = []
    project_node = getProjectNode(state, project_name)
    for task_name in project_node.task_names:
        tasks.append(getTask(state, project_name, task_name))
    return redirect(url_for('render'))


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

def getTask(state, project_name,task_name):
    ''' Given a project name and task name get a task node. '''
    
    # make address of task node
    task_address = addressing.make_task_address(project_name, task_name)
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
        if location['address'] == address:
            encoded_data = location['data']
            return base64.b64decode(encoded_data)
    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)
