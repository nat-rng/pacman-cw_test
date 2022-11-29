# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py
from pacman import Directions
from game import Agent
import api
import random
import game
import util

# Size of small map (width*height)
SMALL_MAP = 49
NO_OF_RUNS = 0

#nondeterministic probabilities
INTENDED_ACTION = 0.8
ALTERNATE_ACTION = 0.1


class Coordinates():
    '''
    Sets atrtibutes for point on the map if it is a wall, reward, policy and utility
    '''
    def __init__(self, wall_bool, reward, transition_policy=Directions.STOP, utility=0.0):
        self.wall_bool = wall_bool
        self.reward = reward
        self.transition_policy = transition_policy
        self.utility = utility
   
class MDPAgent(Agent):
    '''
    Agent that makes pacman traverse maze using the Markov Decision Problem
    '''

    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"
    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        #get corners to generate map_x and map_y of map
        corners = api.corners(state)

        #find map_x and map_y
        self.map_x = self.getLayoutWidth(corners)
        self.map_y = self.getLayoutHeight(corners)
        
        self.map_size = self.map_x * self.map_y
        
        global LOOKAHEAD_LIMIT
        global GAMMA_VALUE
        global FOOD_REWARD
        global EMPTY_REWARD 
        global GHOST_REWARD
        global VULNERABLE_GHOST_REWARD
        global CAPSULES_REWARD
        
        if self.map_size > SMALL_MAP: 
            LOOKAHEAD_LIMIT = 4 #4
            GAMMA_VALUE = 0.90
            FOOD_REWARD = 20 #20
            EMPTY_REWARD = -0.02
            GHOST_REWARD = -45 #40
            VULNERABLE_GHOST_REWARD = 30 #30
            CAPSULES_REWARD = 5#5
        else:
            LOOKAHEAD_LIMIT = 3 #3
            GAMMA_VALUE = 0.50 #0.5
            FOOD_REWARD = 80 #80
            EMPTY_REWARD = -0.05 #-0.05
            GHOST_REWARD = -5 #-5
            VULNERABLE_GHOST_REWARD = 0
            CAPSULES_REWARD = 0

        #Code was modified from the provided mapAgents.py file from Practical 5    
        #create placeholder game_state (a matrix with empty space coordinantes)
        self.game_state = [[Coordinates(False, EMPTY_REWARD) for _ in range(self.map_y)] for _ in range(self.map_x)] 

        self.initializeMapStates(state)
        #get height of maze  
 
    def getLayoutHeight(self, corners):
        map_y = -1
        for i in range(len(corners)):
            if corners[i][1] > map_y:
                map_y = corners[i][1]
        return map_y + 1

    #get width of maze
    def getLayoutWidth(self, corners):
        map_x = -1
        for i in range(len(corners)):
            if corners[i][0] > map_x:
                map_x = corners[i][0]
        return map_x + 1

    def initializeMapStates(self, state):
        #generate imp lists     
        self.walls = api.walls(state)
        self.grid = [(i,j) for i in range(self.map_x) for j in range(self.map_y)] 
        ghosts = api.ghosts(state)
        capsules = api.capsules(state)
        foods = api.food(state)
        #initialize 2d array with arbitrary values of MapCoordinate class
        for wall in self.walls:
            self.game_state[wall[0]][wall[1]] = Coordinates(True, None)

        for capsule in capsules:
            self.game_state[capsule[0]][capsule[1]] = Coordinates(False, CAPSULES_REWARD)

        for food in foods:
            self.game_state[food[0]][food[1]] = Coordinates(False, FOOD_REWARD)

        for ghost in ghosts:
            self.game_state[ghost[0]][ghost[1]] = Coordinates(False, GHOST_REWARD)

    # This is what gets run in between multiple games
    def final(self, state):
        global NO_OF_RUNS 
        NO_OF_RUNS += 1
        # if NO_OF_RUNS % 25 == 0:
        #     initial_radius = GHOST_RADIUS
        #     GHOST_RADIUS += 1
        #     print "GHOST_RADIUS increased from {} to {}".format(initial_radius, GHOST_RADIUS)
        print "Looks like the game just ended!"
        print "This was run number: " + str(NO_OF_RUNS)
 
    #update the map with new values of rewards and symbols
    def updateRewards(self, state):    
        self.ghost_locations = api.ghostStatesWithTimes(state)
        self.capsules = api.capsules(state)
        self.foods = api.food(state)
        self.accessible_to_ghosts = self.accessibleGhostFields(state)

        if self.map_size > SMALL_MAP:
            if self.map_x % 2 == 0 and self.map_y % 2 != 0:
                self.ghost_home = [((self.map_x / 2) - 2, ((self.map_y + 1) / 2) - 1),
                                      ((self.map_x / 2) - 1, ((self.map_y + 1) / 2) - 1),
                                      ((self.map_x / 2), ((self.map_y + 1) / 2) - 1),
                                      ((self.map_x / 2) - 1, ((self.map_y + 1) / 2)),
                                      ((self.map_x / 2), ((self.map_y + 1) / 2)),
                                      ((self.map_x / 2) + 1, ((self.map_y + 1) / 2) - 1)]
        else:
            self.ghost_home = []

        for coord in self.grid:
            if coord not in self.walls and coord not in self.foods:
                self.game_state[int(coord[0])][int(coord[1])].reward = EMPTY_REWARD

        for capsule in self.capsules:
            self.game_state[capsule[0]][capsule[1]].reward = CAPSULES_REWARD

        for food in self.foods:
            num_walls = len({(food[0]+1, food[1]), (food[0]-1, food[1]), (food[0], food[1]+1), (food[0], food[1]-1)}.intersection(self.walls))
            if len(self.foods) == 1:
                self.game_state[food[0]][food[1]].reward = FOOD_REWARD**FOOD_REWARD
            else:
                self.game_state[food[0]][food[1]].reward = FOOD_REWARD / (1 + num_walls)

        vulnerable_ghosts = [self.ghost_locations[i][0] for i in range(len(self.ghost_locations)) if self.ghost_locations[i][1] > 0]
        vulnerable_time = [self.ghost_locations[i][1] for i in range(len(self.ghost_locations)) if self.ghost_locations[i][1] > 0]
        if vulnerable_time and vulnerable_time[0] > 2:
            if len(vulnerable_ghosts) > 1:
                for fields,i in zip(self.accessible_to_ghosts, range(len(self.accessible_to_ghosts))):
                    for coord in fields:
                        self.game_state[int(coord[0])][int(coord[1])].reward = ((vulnerable_time[0])+VULNERABLE_GHOST_REWARD) / (1 + i)
            else:
                vulnerable_ghost_fields = [vulnerable_ghosts]
                duplicate_fields = set()
                duplicate_fields.update(vulnerable_ghosts)
                self.ghostLookAhead(state, vulnerable_ghost_fields, duplicate_fields, LOOKAHEAD_LIMIT)

                for fields,i in zip(self.accessible_to_ghosts, range(len(self.accessible_to_ghosts))):
                    for coord in fields:
                        self.game_state[int(coord[0])][int(coord[1])].reward = GHOST_REWARD / (1 + i)
                
                for vuln_fields,i in zip(vulnerable_ghost_fields, range(len(vulnerable_ghost_fields))):
                    for vuln_coord in vuln_fields:
                        self.game_state[int(vuln_coord[0])][int(vuln_coord[1])].reward = ((vulnerable_time[0]**0.8)+VULNERABLE_GHOST_REWARD) / (1 + i)
        else:
            for fields,i in zip(self.accessible_to_ghosts, range(len(self.accessible_to_ghosts))):
                for coord in fields:
                    if coord in self.foods:
                        self.game_state[int(coord[0])][int(coord[1])].reward = (FOOD_REWARD / (1 + num_walls)) + (GHOST_REWARD / (1 + i))
                        # print self.game_state[int(coord[0])][int(coord[1])].reward, "FOOD_REWARD + (GHOST_REWARD / (1 + i))"
                    else:
                        self.game_state[int(coord[0])][int(coord[1])].reward = GHOST_REWARD / (1 + i)


        for ghost_spawn in self.ghost_home:
            self.game_state[ghost_spawn[0]][ghost_spawn[1]].reward = -1000

    def accessibleGhostFields(self, state):
        ghosts = api.ghosts(state)
        accessible_fields = [ghosts]
        duplicate_fields = set()
        duplicate_fields.update(ghosts)
        self.ghostLookAhead(state, accessible_fields, duplicate_fields, LOOKAHEAD_LIMIT)
        return accessible_fields

    def ghostLookAhead(self, state, accessible_fields, duplicates, limit):
        index_locations = []
        duplicate_fields = duplicates
        for field in accessible_fields:
            for i in range(len(field)):
                ghost_moves = ((int(field[i][0])+1,int(field[i][1])), (int(field[i][0])-1,int(field[i][1])), (int(field[i][0]),int(field[i][1])+1), (int(field[i][0]),int(field[i][1])-1))
                for move in ghost_moves:
                    if move not in self.walls and move not in duplicate_fields:
                        index_locations.append(move)
                        duplicate_fields.add(move)
        accessible_fields.append(index_locations)
        if limit > 1:
            return self.ghostLookAhead(state, accessible_fields, duplicate_fields, limit-1)
        return accessible_fields
 
    #method for calculating updating all the utilities and policies in self.game_state        
    def updateUtilitiesAndTransitions(self, state):
        #create copy of game state and iniitialize utilities with arbitrary values (i.e. 0.0) 
        converging_states = self.game_state
        previous_utilities = [0.0 for _ in range(self.map_x) for _ in range(self.map_y)]
        iterate = True
        # iteration = 0
        #loop until utility values converge
        while iterate == True:
            new_utilities = []
            # calculate new utilities and save in temporary 2d array
            terminal_states = []
            if len(api.food(state)) == 1:
                terminal_states = terminal_states + self.foods
            for row in range(self.map_y):
                for col in range(self.map_x):
                    #if current pos not a wall, calculate new utility of pos
                    if (self.game_state[col][row].wall_bool == False and (col,row) not in terminal_states):
                        expected_utility = self.getMaxUtility(converging_states, col, row)
                        converging_states[col][row].utility = converging_states[col][row].reward + GAMMA_VALUE * expected_utility
                        new_utilities.append(converging_states[col][row].utility)
                
                #copy over converging_states utitities to game_state
                self.game_state[col][row].utility = converging_states[col][row].utility

            convergence = [new==old for new,old in zip(new_utilities, previous_utilities)]
            if sum(convergence)/len(convergence) == 1:
                iterate = False
                    
            previous_utilities = new_utilities
        #     iteration += 1
        # print iteration
        pacman_pos = api.whereAmI(state)
        self.game_state[pacman_pos[0]][pacman_pos[1]].transition_policy = self.getPolicy(pacman_pos)
                    
        # map_view = []
        # for row in range(self.map_y):
        #     row_values = []
        #     for col in range(self.map_x):
        #         row_values.append(self.game_state[col][row].utility)
        #     map_view.append(row_values)
        # for item in map_view[::-1]:
        #     print(item)
        # print ' _ '*2*self.map_x

    def getPolicy(self, pacman_pos):
        expected_utilities = [(self.game_state[pacman_pos[0]][pacman_pos[1]+1].utility, Directions.NORTH),
                              (self.game_state[pacman_pos[0]][pacman_pos[1]-1].utility, Directions.SOUTH),
                              (self.game_state[pacman_pos[0]+1][pacman_pos[1]].utility, Directions.EAST),
                              (self.game_state[pacman_pos[0]-1][pacman_pos[1]].utility, Directions.WEST)]
        pacman_surrounding = [(pacman_pos[0], pacman_pos[1]+1), (pacman_pos[0], pacman_pos[1]-1), 
                              (pacman_pos[0]+1, pacman_pos[1]), (pacman_pos[0]-1, pacman_pos[1])]
        wall_index = ()
        # print expected_utilities
        # print pacman_surrounding
        for direction in pacman_surrounding:
            if direction in self.walls:
                wall_index += (pacman_surrounding.index(direction),)
        expected_utilities = [expected_utilities[i] for i in range(len(expected_utilities)) if i not in wall_index]
        # print wall_index
        # print expected_utilities
        expected_utilities = list(zip(*expected_utilities))
        # print expected_utilities[0]
        max_policy_index = expected_utilities[0].index(max(expected_utilities[0]))
        max_policy = expected_utilities[1][max_policy_index]
        return max_policy
    
    def getMaxUtility(self, game_state, col, row):  
        expected_utilities = []
        expected_utilities.append(self.calculateExpUtility(game_state[col][row], game_state[col][row+1], game_state[col-1][row], game_state[col+1][row]))
        expected_utilities.append(self.calculateExpUtility(game_state[col][row], game_state[col][row-1], game_state[col+1][row], game_state[col-1][row]))
        expected_utilities.append(self.calculateExpUtility(game_state[col][row], game_state[col+1][row], game_state[col][row+1], game_state[col][row-1]))
        expected_utilities.append(self.calculateExpUtility(game_state[col][row], game_state[col-1][row], game_state[col][row-1], game_state[col][row+1]))
        #find index of max in lis
        
        max_utility = max(expected_utilities)
            
        return max_utility
        
    #method to calculate utility of moving from state s to s'
    def calculateExpUtility(self, current_pos, intended_move, alt_move_one, alt_move_two):
        wall_move = [m for m in [intended_move, alt_move_one, alt_move_two] if m.wall_bool == True]
        if wall_move:
            for move in wall_move:
                move = current_pos

        exp_utility = INTENDED_ACTION*intended_move.utility + ALTERNATE_ACTION*alt_move_one.utility + ALTERNATE_ACTION*alt_move_two.utility
        
        return exp_utility
 
    def getAction(self, state):
        # update map 
        self.updateRewards(state)
        
        #calculate new utilities and policies and save in self.game_state
        self.updateUtilitiesAndTransitions(state)
        
        #get all legal actions at current pacman pos
        legal = api.legalActions(state)
        
        #get pacman pos
        pacman_pos = api.whereAmI(state)
        
        #get the policy saved on pacmans current pos
        move_to_make = self.game_state[pacman_pos[0]][pacman_pos[1]].transition_policy

        #make move
        return api.makeMove(move_to_make, legal)
    