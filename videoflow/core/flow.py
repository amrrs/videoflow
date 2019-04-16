from .node import Node, ProducerNode, ConsumerNode, ProcessorNode
from .execution import allocate_task

def create_vertex_set(producers):
    V = set()
    for node in producers:
        V.add(node)
        for child in node.children:
            V.add(child)
    return V

def has_cycle_util(v : Node, visited, rec):
    visited[v] = True
    rec[v] = True
    
    for child in v.children:
        if visited[child] == False:
            if has_cycle_util(child, visited, rec):
                return True
        elif rec[child] == True:
            return True
    
    rec[v] = False
    return False

def has_cycle(producers):
    V = create_vertex_set(producers)
    visited = {}
    rec = {}
    for v in V:
        visited[v] = False
        rec[v] = False
    
    for v in V:
        if visited[v] == False:
            if has_cycle_util(v, visited, rec):
                return True
    return False
    
def topological_sort_util(v : Node, visited, stack):
    visited[v] = True
    for child in v.children:
        topological_sort_util(child, visited, stack)
    stack.insert(0, v)

def topological_sort(producers):
    V = create_vertex_set(producers)
    visited = {}
    for v in V:
        visited[v] = False
    stack = []

    for v in V:
        if visited[v] == False:
            topological_sort_util(v, visited, stack)
    
    return stack

class Flow:
    def __init__(self, producers, consumers):
        if len(producers) != 1:
            raise AttributeError('Only support flows with 1 producer for now.')
        self._producers = producers
        self._consumers = consumers

    def _compile(self):
        pass

    def start(self):
        '''
        Starts the flow
        '''

        #1. Build a topological sort of the graph.
        if has_cycle(self._producers):
            raise ValueError('Cycle found in graph')

        tsort = topological_sort(self._producers)

        #2. TODO: OPtimize graph in the following ways:   
        # a) Tasks do not need to pass down to children
        # all of the outputs of parents.  Hence, at a given
        # level of the topological sort, have the list of 
        # inputs from parents that are not needed below that 
        # level

        # b) Not all the processors have to write to a pub/sub channel
        # If their output is only needed by the next preprocessor and non one
        # else below in the graph, then I can string subsequent preprocessors together
        # a big preprocessor
        
        #3. Create the tasks and the input/outputs
        # for them
        tasks = []
        for i in range(len(tsort)):
            node = tsort[i]
            
            if isinstance(node, ProducerNode):
                task = ProducerTask(node)
            elif isinstance(node, ProcessorNode):
                task = ProcessorTask(
                    node, 
                    tasks[i - 1].output_channel,
                    [p.id for p in node.parents]
                )
            elif isinstance(node, ConsumerNode):
                task = ConsumerTask(
                    node,
                    tasks[i - 1].output_channel,
                    [p.id for p in node.parents]
                )
            else:
                raise ValueError('node is not of one of the valid types')
            tasks.append(task)
        
        # 4. Put each task to run in the place where the processor it
        # contains inside runs.
        for task in tasks:
            allocate_task(task)
        
        
    def stop(self):
        '''
        It should deallocate all the resources and stop the flow in an organic way.
        '''
        pass