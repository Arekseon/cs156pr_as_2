"""Implement Agents and Environments (Chapters 1-2).

The class hierarchies are as follows:

Object ## A physical object that can exist in an environment
    Agent
        Wumpus
        RandomAgent
        ReflexVacuumAgent
        ...
    Dirt
    Wall
    ...
    
Environment ## An environment holds objects, runs simulations
    XYEnvironment
        VacuumEnvironment
        WumpusEnvironment

EnvFrame ## A graphical representation of the Environment

"""
TIME_DELAY = 0.5

import random, copy, math, sys,time

#______________________________________________________________________________

class Object:
    """This represents any physical object that can appear in an Environment.
    You subclass Object to get the objects you want.  Each object can have a
    .__name__  slot (used for output only)."""
    def __repr__(self):
        return '<%s>' % getattr(self, '__name__', self.__class__.__name__)

    def is_alive(self):
        """Objects that are 'alive' should return true."""
        return hasattr(self, 'alive') and self.alive

    def display(self, canvas, x, y, width, height):
        """Display an image of this Object on the canvas."""
        pass

class Agent(Object):
    """An Agent is a subclass of Object with one required slot,
    .program, which should hold a function that takes one argument, the
    percept, and returns an action. (What counts as a percept or action
    will depend on the specific environment in which the agent exists.) 
    Note that 'program' is a slot, not a method.  If it were a method,
    then the program could 'cheat' and look at aspects of the agent.
    It's not supposed to do that: the program can only look at the
    percepts.  An agent program that needs a model of the world (and of
    the agent itself) will have to build and maintain its own model.
    There is an optional slots, .performance, which is a number giving
    the performance measure of the agent in its environment."""

    def __init__(self):
        def program(percept):
            return raw_input('Percept=%s; action? ' % percept)
        self.program = program
        self.alive = True

def TraceAgent(agent):
    """Wrap the agent's program to print its input and output. This will let
    you see what the agent is doing in the environment."""
    old_program = agent.program
    def new_program(percept):
        action = old_program(percept)
        print '%s perceives %s and does %s' % (agent, percept, action)
        return action
    agent.program = new_program
    return agent

#______________________________________________________________________________

class TableDrivenAgent(Agent):
    """This agent selects an action based on the percept sequence.
    It is practical only for tiny domains.
    To customize it you provide a table to the constructor. [Fig. 2.7]"""
    
    def __init__(self, table):
        "Supply as table a dictionary of all {percept_sequence:action} pairs."
        ## The agent program could in principle be a function, but because
        ## it needs to store state, we make it a callable instance of a class.
        Agent.__init__(self)
        percepts = []
        def program(percept):
            percepts.append(percept)
            action = table.get(tuple(percepts))
            return action
        self.program = program


class RandomAgent(Agent):
    "An agent that chooses an action at random, ignoring all percepts."
    def __init__(self, actions):
        Agent.__init__(self)
        self.program = lambda percept: random.choice(actions)


#______________________________________________________________________________

loc_A, loc_B = (0, 0), (1, 0) # The two locations for the Vacuum world

class ReflexVacuumAgent(Agent):
    "A reflex agent for the two-state vacuum environment. [Fig. 2.8]"

    def __init__(self):
        Agent.__init__(self)
        def program((location, status)):
            if status == 'Dirty': return 'Suck'
            elif location == loc_A: return 'Right'
            elif location == loc_B: return 'Left'
        self.program = program


def RandomVacuumAgent():
    "Randomly choose one of the actions from the vaccum environment."
    return RandomAgent(['Right', 'Left', 'Suck', 'NoOp'])


def TableDrivenVacuumAgent():
    "[Fig. 2.3]"
    table = {((loc_A, 'Clean'),): 'Right',
             ((loc_A, 'Dirty'),): 'Suck',
             ((loc_B, 'Clean'),): 'Left',
             ((loc_B, 'Dirty'),): 'Suck',
             ((loc_A, 'Clean'), (loc_A, 'Clean')): 'Right',
             ((loc_A, 'Clean'), (loc_A, 'Dirty')): 'Suck',
             # ...
             ((loc_A, 'Clean'), (loc_A, 'Clean'), (loc_A, 'Clean')): 'Right',
             ((loc_A, 'Clean'), (loc_A, 'Clean'), (loc_A, 'Dirty')): 'Suck',
             # ...
             }
    return TableDrivenAgent(table)


class ModelBasedVacuumAgent(Agent):
    "An agent that keeps track of what locations are clean or dirty."
    def __init__(self):
        Agent.__init__(self)
        model = {loc_A: None, loc_B: None}
        def program((location, status)):
            "Same as ReflexVacuumAgent, except if everything is clean, do NoOp"
            model[location] = status ## Update the model here
            if model[loc_A] == model[loc_B] == 'Clean': return 'NoOp'
            elif status == 'Dirty': return 'Suck'
            elif location == loc_A: return 'Right'
            elif location == loc_B: return 'Left'
        self.program = program
        
#______________________________________________________________________________

class Environment:
    """Abstract class representing an Environment.  'Real' Environment classes
    inherit from this. Your Environment will typically need to implement:
        percept:           Define the percept that an agent sees.
        execute_action:    Define the effects of executing an action.
                           Also update the agent.performance slot.
    The environment keeps a list of .objects and .agents (which is a subset
    of .objects). Each agent has a .performance slot, initialized to 0.
    Each object has a .location slot, even though some environments may not
    need this."""

    def __init__(self,):
        self.objects = []; self.agents = []

    object_classes = [] ## List of classes that can go into environment

    def percept(self, agent):
	"Return the percept that the agent sees at this point. Override this."
        abstract

    def execute_action(self, agent, action):
        "Change the world to reflect this action. Override this."
        abstract

    def default_location(self, object):
	"Default location to place a new object with unspecified location."
        return None

    def exogenous_change(self):
	"If there is spontaneous change in the world, override this."
	pass

    def is_done(self):
        "By default, we're done when we can't find a live agent."
        for agent in self.agents:
            if agent.is_alive(): return False
        return True

    def step(self):
	"""Run the environment for one time step. If the
	actions and exogenous changes are independent, this method will
	do.  If there are interactions between them, you'll need to
	override this method."""
	if not self.is_done():
            actions = [agent.program(self.percept(agent))
                       for agent in self.agents]
            for (agent, action) in zip(self.agents, actions):
		self.execute_action(agent, action)
            self.exogenous_change()

    def run(self, steps=1000):
	"""Run the Environment for given number of time steps."""
	for step in range(steps):
            if self.is_done(): return
            self.step()

    def add_object(self, object, location=None):
	"""Add an object to the environment, setting its location. Also keep
	track of objects that are agents.  Shouldn't need to override this."""
	object.location = location or self.default_location(object)
	self.objects.append(object)
	if isinstance(object, Agent):
            object.performance = 0
            self.agents.append(object)
	return self
    

class XYEnvironment(Environment):
    """This class is for environments on a 2D plane, with locations
    labelled by (x, y) points, either discrete or continuous.  Agents
    perceive objects within a radius.  Each agent in the environment
    has a .location slot which should be a location such as (0, 1),
    and a .holding slot, which should be a list of objects that are
    held """

    def __init__(self, width=10, height=10):
        update(self, objects=[], agents=[], width=width, height=height)

    def objects_at(self, location):
        "Return all objects exactly at a given location."
        return [obj for obj in self.objects if obj.location == location]

    def objects_near(self, location, radius):
        "Return all objects within radius of location."
        radius2 = radius * radius
        return [obj for obj in self.objects
                if distance2(location, obj.location) <= radius2]

    def percept(self, agent):
        "By default, agent perceives objects within radius r."
        return [self.object_percept(obj, agent)
                for obj in self.objects_near(agent)]

    def execute_action(self, agent, action):
        if action == 'TurnRight':
            agent.heading = turn_heading(agent.heading, -1)
        elif action == 'TurnLeft':
            agent.heading = turn_heading(agent.heading, +1)
        elif action == 'Forward':
            self.move_to(agent, vector_add(agent.heading, agent.location))
        elif action == 'Grab':
            objs = [obj for obj in self.objects_at(agent.location)
                    if obj.is_grabable(agent)]
            if objs:
                agent.holding.append(objs[0])
        elif action == 'Release':
            if agent.holding:
                agent.holding.pop()
        agent.bump = False

    def object_percept(self, obj, agent): #??? Should go to object?
        "Return the percept for this object."
        return obj.__class__.__name__

    def default_location(self, object):
        return (random.choice(self.width), random.choice(self.height))

    def move_to(object, destination):
        "Move an object to a new location."
        
    def add_object(self, object, location=(1, 1)):
        Environment.add_object(self, object, location)
        object.holding = []
        object.held = None
        self.objects.append(object)

    def add_walls(self):
        "Put walls around the entire perimeter of the grid."
        for x in range(self.width):
            self.add_object(Wall(), (x, 0))
            self.add_object(Wall(), (x, self.height-1))
        for y in range(self.height):
            self.add_object(Wall(), (0, y))
            self.add_object(Wall(), (self.width-1, y))

def turn_heading(heading, inc,
                 headings=[(1, 0), (0, 1), (-1, 0), (0, -1)]):
    "Return the heading to the left (inc=+1) or right (inc=-1) in headings."
    return headings[(headings.index(heading) + inc) % len(headings)]  

#______________________________________________________________________________
## Vacuum environment 

class TrivialVacuumEnvironment(Environment):
    """This environment has two locations, A and B. Each can be Dirty or Clean.
    The agent perceives its location and the location's status. This serves as
    an example of how to implement a simple Environment."""

    def __init__(self):
        Environment.__init__(self)
        self.status = {loc_A:random.choice(['Clean', 'Dirty']),
                       loc_B:random.choice(['Clean', 'Dirty'])}
        
    def percept(self, agent):
        "Returns the agent's location, and the location status (Dirty/Clean)."
        return (agent.location, self.status[agent.location])

    def execute_action(self, agent, action):
        """Change agent's location and/or location's status; track performance.
        Score 10 for each dirt cleaned; -1 for each move."""
        if action == 'Right':
            agent.location = loc_B
            agent.performance -= 1
        elif action == 'Left':
            agent.location = loc_A
            agent.performance -= 1
        elif action == 'Suck':
            if self.status[agent.location] == 'Dirty':
                agent.performance += 10
            self.status[agent.location] = 'Clean'

    def default_location(self, object):
        "Agents start in either location at random."
        return random.choice([loc_A, loc_B])

class Dirt(Object): pass
class Wall(Object): pass

class VacuumEnvironment(XYEnvironment):
    """The environment of [Ex. 2.12]. Agent perceives dirty or clean,
    and bump (into obstacle) or not; 2D discrete world of unknown size;
    performance measure is 100 for each dirt cleaned, and -1 for
    each turn taken."""
    def __init__(self, width=10, height=10):
        XYEnvironment.__init__(self, width, height)
        self.add_walls()

    object_classes = [Wall, Dirt, ReflexVacuumAgent, RandomVacuumAgent,
                      TableDrivenVacuumAgent, ModelBasedVacuumAgent]

    def percept(self, agent):
        """The percept is a tuple of ('Dirty' or 'Clean', 'Bump' or 'None').
        Unlike the TrivialVacuumEnvironment, location is NOT perceived."""
        status =  if_(self.find_at(Dirt, agent.location), 'Dirty', 'Clean')
        bump = if_(agent.bump, 'Bump', 'None')
        return (status, bump)

    def execute_action(self, agent, action):
        if action == 'Suck':
            if self.find_at(Dirt, agent.location):
                agent.performance += 100
        agent.performance -= 1
        XYEnvironment.execute_action(self, agent, action)

#______________________________________________________________________________

class SimpleReflexAgent(Agent):
    """This agent takes action based solely on the percept. [Fig. 2.13]"""

    def __init__(self, rules, interpret_input):
        Agent.__init__(self)
        def program(percept):
            state = interpret_input(percept)
            rule = rule_match(state, rules)
            action = rule.action
            return action
        self.program = program

class ReflexAgentWithState(Agent):
    """This agent takes action based on the percept and state. [Fig. 2.16]"""

    def __init__(self, rules, udpate_state):
        Agent.__init__(self)
        state, action = None, None
        def program(percept):
            state = update_state(state, action, percept)
            rule = rule_match(state, rules)
            action = rule.action
            return action
        self.program = program

#______________________________________________________________________________
## The Wumpus World

class Gold(Object): pass
class Pit(Object): pass
class Arrow(Object): pass
class Wumpus(Object): pass
class Explorer(Agent): pass

class WumpusEnvironment(XYEnvironment):
    object_classes = [Wall, Gold, Pit, Arrow, Wumpus, Explorer]
    def __init__(self, width=10, height=10):
        self.objects=[]
        self.agents=[]
        self.width=width
        self.height=height
        self.score = 0
        self.log = ""
        self.steps = 0
        self.Scream = False
        # XYEnvironment.__init__(self, width, height)
        self.add_walls()

############################################################################


    def percept(self, agent):
        location = agent.location
        direction = agent.direction
        Stench = False
        Breeze = False
        Glitter = False
        Bump = agent.Bump #hit wall
        agent.Bump = False
        Scream = self.Scream#killed wambus
        for obj in self.objects_near(agent.location, radius=1):
            if isinstance(obj, Pit):
                Breeze = True
            elif isinstance(obj, Wumpus):
                Stench = True
        for obj in self.objects_at(agent.location):
            if isinstance(obj, Gold):
                Glitter = True
        # return [self.object_percept(obj, agent) for obj in self.objects_near(agent.location, radius=1)]
        return location, direction, Stench, Breeze, Glitter, Bump, Scream

       

    # def objects_at(self, location):
    #     "Return all objects exactly at a given location."
    #     return [obj for obj in self.objects if obj.location == location]

    def objects_near(self, location, radius):


        "Return all objects within radius of location."
        radius2 = radius * radius
        return [obj for obj in self.objects
                if distance2(location, obj.location) <= radius2]


    def step(self):
        if not self.is_done():
            actions = [agent.program(self.percept(agent))
                       for agent in self.agents]
            for (agent, action) in zip(self.agents, actions):
                self.execute_action(agent, action)
            clear_screen()
            self.steps+=1
            self.draw_grid()
            time.sleep(TIME_DELAY)
            self.exogenous_change()

    def exogenous_change(self):
        if self.Scream:
            self.Scream = False


    def execute_action(self, agent, action):
        if action == 'TurnRight':
            agent.direction = turn_heading(agent.direction, +1)
        elif action == 'TurnLeft':
            agent.direction = turn_heading(agent.direction, -1)
        elif action == 'Forward':
            new_location = update_location(agent.location,agent.direction)
            # print new_location
            can_move = True
            for obj in self.objects_at(new_location):
                if isinstance(obj, Wall):
                    agent.Bump = True
                    can_move = False
                    self.log = "{}\n #{}{}: {} hit the wall".format(
                        self.log,"0"*(3-len(str(self.steps))), self.steps, 
                        agent.__class__.__name__)
                elif isinstance(obj, Pit) or isinstance(obj, Wumpus):
                    self.log = "{}\n #{}{}: {} meats {} and dies(-1000 points)".format(
                        self.log,"0"*(3-len(str(self.steps))), self.steps,
                        agent.__class__.__name__, obj.__class__.__name__)
                    # print"agent meats {} and dies".format(obj.__class__.__name__)
                    self.score-=1000
                    can_move = False
                    agent.is_alive = False
                    self.agents.remove(agent)
                    self.objects.remove(agent)
            if can_move:
                agent.location=new_location
                self.score-=1

        elif action == 'Grab':
            for obj in self.objects_at(agent.location):
                if isinstance(obj, Gold):
                    self.log = "{}\n #{}{}: {} grabbed the Gold(+1000 points)".format(
                        self.log,"0"*(3-len(str(self.steps))), self.steps,
                        agent.__class__.__name__)
                    self.score+=1000
                    agent.holding = obj
                    self.objects.remove(obj)
        #rewrite
        elif action == 'Release':
            if agent.holding:
                agent.holding.pop()

        elif action == 'Shoot':
            self.log = "{}\n #{}{}: {} shoot an arrow(-10 points)".format(
                        self.log,"0"*(3-len(str(self.steps))), self.steps,
                        agent.__class__.__name__)
            arrow_location = agent.location
            self.score-=10
            for i in xrange(max(self.width, self.height)):
                arrow_location=update_location(arrow_location,agent.direction)
                for obj in self.objects_at(arrow_location):
                    if isinstance(obj, Wumpus):
                        self.log = "{}\n #{}{}: {} killed Wumpus".format(
                        self.log,"0"*(3-len(str(self.steps))), self.steps,
                        agent.__class__.__name__)
                        self.objects.remove(obj)
                        self.Scream = True

        agent.bump = False
        
    def add_object(self, object, location=(1, 1), direction=(1,0)):
        Environment.add_object(self, object, location)
        object.holding = []
        object.held = None
        object.location = location
        if isinstance(object, Agent):
            object.direction = direction
            object.Bump = False


    def add_walls(self):
        "Put walls around the entire perimeter of the grid."
        for x in xrange(1, self.width-1):
            self.add_object(Wall(), (x, 0))
            self.add_object(Wall(), (x, self.height-1))
        for y in xrange(self.height):
            self.add_object(Wall(), (0, y))
            self.add_object(Wall(), (self.width-1, y))

    def draw_grid(self):
        print"________"*self.width + "_"
        for y in xrange(self.height-1,-1,-1):
            print"|", 
            for x in xrange(self.width):
                to_print = ""
                for obj in self.objects_at((y,x)):
                    if isinstance(obj, Gold):
                        to_print+="G"
                    if isinstance(obj, Agent):
                        if obj.direction == (1,0):
                            to_print+="A"
                        if obj.direction == (-1,0):
                            to_print+="V"
                        if obj.direction == (0,-1):
                            to_print+="<"
                        if obj.direction == (0,1):
                            to_print+=">"
                    if isinstance(obj, Wumpus):
                        to_print+="W"
                    if isinstance(obj, Pit):
                        to_print+="P"
                    if isinstance(obj, Wall):
                        to_print+="######"
                print to_print+" "*(6-len(to_print)) + "|",
            print""
        print"________"*self.width + "_"
        print"Score: {}".format(self.score)
        print self.log
        # for agent in self.agents:
        #     print"agent {} is {}".format(agent.__class__.__name__, "alive" if agent.is_alive() else "dead")

    def is_done(self):
        for agent in self.agents:
            return False
        return True
        
def distance2(location1, location2):
        return math.sqrt(math.pow(location1[0] - location2[0],2) 
                        + math.pow(location1[1] - location2[1],2)) 

def update_location(location, vector):
    return (location[0]+vector[0],location[1]+vector[1])
    
########################################################################
class WumpusWorldAgent(Agent):
    """This agent takes action based solely on the percept. [Fig. 2.13]"""

    def __init__(self):
        Agent.__init__(self)
        self.alive = True
        self.i_heard_scream = False
        self.previous_action = "Forward"
        def program(percept):
            location, direction, Stench, Breeze, Glitter, Bump, Scream = percept
            if Scream:
                self.i_heard_scream = True
            if Glitter:
                action = "Grab"
            elif Bump:
                action = "TurnRight"
            elif Breeze and self.previous_action=="Forward":
                action = "TurnRight"
            elif Stench:
                if not self.i_heard_scream:
                    action = "Shoot"
                else:
                    action = "TurnRight"
            else:
                action = "Forward"

            self.previous_action = action
            return action
        self.program = program


    def is_alive(self):
        return self.alive
#______________________________________________________________________________

def compare_agents(EnvFactory, AgentFactories, n=10, steps=1000):
    """See how well each of several agents do in n instances of an environment.
    Pass in a factory (constructor) for environments, and several for agents.
    Create n instances of the environment, and run each agent in copies of 
    each one for steps. Return a list of (agent, average-score) tuples."""
    envs = [EnvFactory() for i in range(n)]
    return [(A, test_agent(A, steps, copy.deepcopy(envs))) 
            for A in AgentFactories]

def test_agent(AgentFactory, steps, envs):
    "Return the mean score of running an agent in each of the envs, for steps"
    total = 0
    for env in envs:
        agent = AgentFactory()
        env.add_object(agent)
        env.run(steps)
        total += agent.performance
    return float(total)/len(envs)


def clear_screen():
    """Clear screen, return cursor to top left"""
    sys.stdout.write('\033[2J')
    sys.stdout.write('\033[H')
    sys.stdout.flush()

if __name__ == "__main__":
    e = WumpusEnvironment(width=10, height=10)
    print("FRESH START")
    e.add_object(WumpusWorldAgent(), location = (1,1), direction= (1,0))
    e.add_object(Gold(), location = (8,3))
    e.add_object(Gold(), location = (3,4))
    e.add_object(Gold(), location = (5,7))
    
    e.add_object(Wumpus() , location = (3,8))
    e.add_object(Pit() , location = (1,3))
    e.add_object(Pit() , location = (4,5))
    e.run(100)
    # for i in xrange(30):
    #     clear_screen()
    #     e.draw_grid()
    #     e.run(1)
    #     time.sleep(0.5)