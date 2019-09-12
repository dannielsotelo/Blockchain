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
    pass

@app.route('/changeaction',methods=['POST'])
def change_action():
    pass

@app.route('/send', methods=['POST'])
def send():
    pass


@app.route('/viewproject',methods=['POST'])
def view_project():
    pass


def getProjectNode(state,project_name):
    ''' Given a project name get a project node. '''
    pass

def getTask(state, project_name,task_name):
    ''' Given a project name and task name get a task node. '''
    pass


def getData(state, address):
    ''' Gets the data from a provided address.

        State has two fields address and data.  We can create the
        address using functions in addressing.py.  The data field
        is encoded with base64 encoding.
    '''
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)