# Utilities
import logging

# Sawtooth SDK
from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError

# Skltn protos
from protobuf.task_pb2 import *
from protobuf.payload_pb2 import *
from protobuf.project_node_pb2 import *

# Skltn addressing specs
import addressing

LOGGER = logging.getLogger(__name__)


class TodoTransactionHandler(TransactionHandler):
    @property
    def family_name(self):
        return addressing.FAMILY_NAME

    @property
    def family_versions(self):
        return ['0.1']

    @property
    def namespaces(self):
        return [addressing.NAMESPACE]

    def apply(self, transaction, state):
        '''
        A Payload consists of a timestamp, an action tag, and
        attributes corresponding to various actions (create_asset,
        touch_asset, etc).  The appropriate attribute will be selected
        depending on the action tag, and that information plus the 
        timestamp and the public key with which the transaction was signed
        will be passed to the appropriate handler function
        unpack_transaction gets the signing key, the timestamp, and the 
        appropriate payload attribute and handler function
        '''
        # TO DO : check that timestamp is valid before calling handler.
        signer, timestamp, payload, handler = _unpack_transaction(transaction, state)

        # note that handler will be chosen by what was given to unpack
        handler(payload, signer, timestamp, state)


# Handler functions

def _create_project(payload, signer, timestamp, state):
    ''' Creates a project metanode and allows tasks to be created

        Takes the project name and makes an address given the METANODE tag 
        that name, and the txn family.  A project name must be unique, the 
        txn will fail if it is not.  
    '''
    # check for complete payload
    if not payload.project_name:
        raise InvalidTransaction(
            "Project must have a name")

    project_address = addressing.make_project_node_address(payload.project_name)
    project_container = _get_container(state,project_address)

    if not project_container: # if no container exists, create one
        project_container = ProjectNodeContainer(entries=[])

    # check to see if a project already exists under the same name
    if any(project_node.project_name == payload.project_name
        for project_node in project_container.entries):
            raise InvalidTransaction(
                'Project with this name already exists.')

    # create the metanode protobuf object
    project_node = ProjectNode(
        project_name = payload.project_name,
        public_keys = [signer]) # add creator of project to authorized public key list

    # add project to container
    project_container.entries.extend([project_node])
    # set state with new project included
    _set_container(state, project_address, project_container)


def _create_task(payload, signer, timestamp, state):
    ''' Creates a task node and adds the task to the project's list of task names

        Takes a task_name and description.  Makes an address given the project
        name and the task name. Each task name must be unique in the
        project.
    '''
    # check for complete payload
    if not payload.project_name:
        raise InvalidTransaction(
           "Project must have a name")
    if not payload.task_name:
        raise InvalidTransaction(
            "Task must have a name.")
    if not payload.description:
        raise InvalidTransaction(
            "Task must have a description.")
    # verify transaction is signed by authorized key
    _verify_contributor(state, signer, payload.project_name)

    # in _create_task(...)
    # find address of project metanode
    project_node_address = addressing.make_project_node_address(payload.project_name)
    # get container of project metanode
    project_node_container = _get_container(state, project_node_address)
    # find the correct project metanode
    for project_node in project_node_container.entries:
        if project_node.project_name == payload.project_name:
            # check to make sure no existing task has the same name and invalidate transaction if one does
            if any(task_name == payload.task_name for task_name in project_node.task_names):
                raise InvalidTransaction(
                    "This task name is already in use.")
            # add new task name to list of task names in project metanode
            project_node.task_names.extend([payload.task_name])
            # set the state of the project metanode with the additional task name
            _set_container(state, project_node_address, project_node_container)

    # in _create_task(...)
    # create the task object
    task = Task (
        project_name = payload.project_name,
        task_name = payload.task_name,
        description = payload.description,
        timestamp = timestamp)
    # make the task address
    task_address = addressing.make_task_address(payload.project_name, payload.task_name)
    # get the container of tasks at the address
    task_container = _get_container(state, task_address)
    # add the task to the container
    task_container.entries.extend([task])
    # set the state at the address
    _set_container(state, task_address, task_container)


def _progress_task(payload, signer, timestamp, state):
    ''' Progress task moves a task along the four possible stages.

        Takes a project name and a task name.  The four stages are
        NOT_STARTED, IN_PROGRESS, TESTING, and DONE.  Moves the 
        task's stage from its current stage to the next if possible.
        It is not possible to progress beyond DONE. 
    '''
    # check for complete payload
    if not payload.project_name:
        raise InvalidTransaction(
            "a project name must be provided")
    if not payload.task_name:
        raise InvalidTransaction(
            "a task name must be provided")
    if not payload.description:
         raise InvalidTransaction(
            'a description must be provided'
    )
    # verify transaction is signed by authorized key
    _verify_contributor(state,signer, payload.project_name)
    #in _progress_task
    # make task address
    task_address = addressing.make_task_address(payload.project_name, payload.task_name)
    # get the container with tasks at this address
    task_container = _get_container(state,task_address)
    # check if it doesn't exist
    if not task_container:
        raise InvalidTransaction(
            "task with specified name does not exist")
    # find the task with the correct name
    for task in task_container.entries:
        if task.task_name == payload.task_name:
            #progress task 
            if task.progress == 0 || task.progress == 1 || task.progress == 2
                task.progress = task.progress + 1
                _set_container(state, task_address, task_container)
            # set the new description and put it in state
            #task.description = payload.description
            #_set_container(state, task_address, task_container)
            return


def _edit_task(payload, signer, timestamp, state):
    ''' Edit a task's description.

        Takes a project name, task name, and task description.
        Only an authorized contributor can make changes, and 
        the project/task must exist.
    '''
    # check for complete payload
    if not payload.project_name:
        raise InvalidTransaction(
            "a project name must be provided")
    if not payload.task_name:
        raise InvalidTransaction(
            "a task name must be provided")
    if not payload.description:
         raise InvalidTransaction(
            'a description must be provided'
    )
    # verify transaction is signed by authorized key
    _verify_contributor(state,signer, payload.project_name)

    # in _edit_task(...)
    # make task address
    task_address = addressing.make_task_address(payload.project_name, payload.task_name)
    # get the container with tasks at this address
    task_container = _get_container(state,task_address)
    # check if it doesn't exist
    if not task_container:
        raise InvalidTransaction(
            "task with specified name does not exist")
    # find the task with the correct name
    for task in task_container.entries:
        if task.task_name == payload.task_name:
            # set the new description and put it in state
            task.description = payload.description
            _set_container(state, task_address, task_container)
        return
    # if task with specified name not found, reject transaction
    raise InvalidTransaction(
        "task with specified name does not exist")


def _add_user(payload, signer, timestamp, state):
    ''' Adds a public key to the list of authorized keys in the project metanode

        Payload should include project name and the new public key
        Transaction must be signed by project owner (0th element of authorized keys list)
    '''
    # check for complete payload
    if not payload.project_name:
        raise InvalidTransaction(
            "a project name must be provided")
    if not payload.task_name:
        raise InvalidTransaction(
            "a task name must be provided")
    if not payload.description:
         raise InvalidTransaction(
            'a description must be provided'
    )
    # verify transaction is signed by authorized key
    _verify_contributor(state,signer, payload.project_name)


def _unpack_transaction(transaction, state):
    '''Return the transaction signing key, the SCPayload timestamp, the
    appropriate SCPayload action attribute, and the appropriate
    handler function (with the latter two determined by the constant
    TYPE_TO_ACTION_HANDLER table.
    '''
    # public key used to sign the transaction
    signer = transaction.header.signer_public_key
    # create an empty Payload object defined in protos/payload.proto
    payload_wrapper = Payload()
    # decode the payload from the binary format
    payload_wrapper.ParseFromString(transaction.payload)
    # define the desired action type indicated by the payload
    action = payload_wrapper.action
    timestamp = payload_wrapper.timestamp

    # in `_unpack_transaction(...)`
    # used to determine which handler function should be used on a certain type of payload
    TYPE_TO_ACTION_HANDLER = {
        Payload.CREATE_PROJECT: ('create_project', _create_project),
        Payload.CREATE_TASK: ('create_task', _create_task),
        Payload.PROGRESS_TASK: ('progress_task', _progress_task),
        Payload.EDIT_TASK: ('edit_task', _edit_task),
        Payload.ADD_USER: ('add_user', _add_user),
    }
    try:
        # get the correct payload field and handler function from the action type
        attribute, handler = TYPE_TO_ACTION_HANDLER[action]
    except KeyError:
        raise Exception('Specified action is invalid')
    # extract the correct payload based on the action type
    payload = getattr(payload_wrapper, attribute)
    # go back to apply
    return signer, timestamp, payload, handler


def _get_container(state, address):
    '''Returns the container at a given address from state'''
    # tag bits that designate the type of node (task/project metanode)
    tag = address[6:8]
    # translate the tag bits to the correct type of container for the node
    containers = { 
        addressing.PROJECT_METANODE : ProjectNodeContainer,
        addressing.TODO_TASK : TaskContainer,
    }   
    # initialize the correct type of container based on
    container = containers[tag]()
    # get the state at the given address
    entries = state.get_state([address])

    if entries:
        data = entries[0].data          # extract the data from the state
        container.ParseFromString(data) # decode data and store in container

    return container


def _set_container(state, address, container):
    '''Sets the state at a certain address to a given container'''
    try:
        addresses = state.set_state({
        address: container.SerializeToString()
        })  
        if not addresses:
            raise InternalError(
                'State error, failed to set state entities')
    except:
        raise InternalError(
            'State error, likely using wrong in/output fields in tx header.')


def _get_project_node(state, project_name):
    '''Returns project metanode of give project name'''
    pass


def _verify_contributor(state, signer, project_name):
    ''' Checks to see if a public key belongs to an authorized contributor of the project.

        Takes the state provided from the apply function, the public key of the signer,
        and the name of the project to check.
        Invalidates the transaction if the public key is not authorized.
    '''
    pass
