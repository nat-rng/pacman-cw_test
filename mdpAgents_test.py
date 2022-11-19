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

GAMMA_VALUE = 0.85
CONVERGENCE_ITERATIONS = 70

#reward values
WALL_REWARD = 0
FOOD_REWARD = 4
GHOST_REWARD = -50
VULNERABLE_GHOST_REWARD = 5
EMPTY_REWARD = -0.5
CAPSULES_REWARD = 4

GHOST_RADIUS =10 #2.1
#nondeterministic probabilities
DETERMINISTIC_ACTION = 0.8
NON_DETERMINISTIC_ACTION = 0.1
NO_OF_RUNS = 0


class GameState():
    '''
    Sets atrtibutes for point on the map if it is a wall, reward, policy and utility
    '''
    
    def __init__(self, wall_bools, rewards, transition_policies, utilities):
        self.wall_bools = wall_bools
        self.rewards = rewards
        self.transition_policies = transition_policies
        self.utilities = utilities
        
    # def __init__(self, wall_bool, reward, transition_policy=Directions.STOP, utility=0.0):
    #     self.wall_bool = wall_bool
    #     self.reward = reward
    #     self.transition_policy = transition_policy
    #     self.utility = utility
   
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
        self.map_x = self.getLayoutWidth(corners)
        self.map_y = self.getLayoutHeight(corners)
        
        wall_bools = [[(i,j) in self.walls for i in range(self.map_x)] for j in range(self.map_y)]
        rewards = [[EMPTY_REWARD for _ in range(self.map_x)] for _ in range(self.map_y)]
        transition_policies = [[Directions.STOP for _ in range(self.map_x)] for _ in range(self.map_y)]
        utilities = [[0.0 for _ in range(self.map_x)] for _ in range(self.map_y)]

        #Code was modified from the provided mapAgents.py file from Practical 5    
        #create placeholder game_state (a matrix with empty space coordinantes)
        self.game_state = GameState(wall_bools, rewards, transition_policies, utilities)

        self.setRewards(state)
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

  
    def setRewards(self, state):
        #generate imp lists     
        self.walls = api.walls(state)
        self.grid = ((i,j) for i in range(self.map_x) for j in range(self.map_y))
        ghosts = api.ghosts(state)
        capsules = api.capsules(state)
        foods = api.food(state)
        #initialize 2d array with arbitrary values of MapCoordinate class
        for wall in self.walls:
            self.game_state.rewards[wall[0]][wall[1]] = WALL_REWARD

        for capsule in capsules:
            self.game_state.rewards[capsule[0]][capsule[1]] = CAPSULES_REWARD

        for food in foods:
            self.game_state.rewards[food[0]][food[1]] = FOOD_REWARD

        for ghost in ghosts:
            self.game_state.rewards[ghost[0]][ghost[1]] = GHOST_REWARD

 
    # This is what gets run in between multiple games
    def final(self, state):
        global NO_OF_RUNS 
        global GHOST_RADIUS
        NO_OF_RUNS += 1
        # if NO_OF_RUNS % 25 == 0:
        #     initial_radius = GHOST_RADIUS
        #     GHOST_RADIUS += 1
        #     print "GHOST_RADIUS increased from {} to {}".format(initial_radius, GHOST_RADIUS)
        print "Looks like the game just ended!"
        print "This was run number: " + str(NO_OF_RUNS)
 
    #update the map with new values of rewards and symbols
    def updateRewards(self, state):    
        ghost_edible = api.ghostStatesWithTimes(state)
        capsules = api.capsules(state)
        foods = api.food(state)
        close_to_ghost = self.ghostRadius(state, GHOST_RADIUS)
        pacman_pos = api.whereAmI(state)

        for coord in self.grid:
            if coord not in self.walls:
                self.game_state.rewards[coord[0]][coord[1]] = EMPTY_REWARD

        for capsule in capsules:
            self.game_state.rewards[capsule[0]][capsule[1]] = CAPSULES_REWARD


        for food in foods:
            num_walls = len(((food[0]+1, food[1]), (food[0]-1, food[1]), (food[0], food[1]+1), (food[0], food[1]-1)).difference(self.walls))
            if len(foods) == 1:
                self.game_state.rewards[food[0]][food[1]] = FOOD_REWARD**num_walls
            else:
                self.game_state.rewards[food[0]][food[1]] = FOOD_REWARD * (1.2**-num_walls)

        for area in close_to_ghost[0]:
            excluded_coords = [self.walls + capsules]
            if((area[0], area[1]) not in set().union(*excluded_coords)):
                index = close_to_ghost[0].index((area[0], area[1]))
                manhatten_distance = close_to_ghost[1][index]
                for i in range(len(ghost_edible)):
                    if ghost_edible[i][1] > 0:
                        self.game_state.reward[area[0]][area[1]] += ghost_edible[i][1]*VULNERABLE_GHOST_REWARD - GHOST_RADIUS*manhatten_distance
                    else:
                        self.game_state.reward[area[0]][area[1]] += GHOST_REWARD + (GHOST_RADIUS**0.5)*manhatten_distance
        
        #find pacman position on map and set reward to 0.0
        self.game_state.reward[pacman_pos[0]][pacman_pos[1]] = 0.0

        for row in range(self.map_y):
            row_values = []
            for col in range(self.map_x):
                row_values.append(self.game_state[col][row].reward)
            print(row_values)
        print ' _ '*2*self.map_x

    
    def ghostRadius(self, state, limit):
        ghosts = api.ghosts(state)
        withinLimit = set()
        
        for ghost in ghosts:
            for i in range(len(self.grid)):
                manhattanDistance = util.manhattanDistance(ghost,self.grid[i])
                if manhattanDistance <= limit:
                    withinLimit.add((self.grid[i],manhattanDistance))

        dual_list = list(map(list, zip(*withinLimit)))
        return dual_list
 
    #method for calculating updating all the utilities and policies in self.game_state        
    def updateUtilitiesAndTransitions(self, state):
        #list to choose a move from based on calculation from the method updatePolicy
        directions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST, Directions.STOP]
        
        #initialise arbitrary list of utilities for each state
        converging_utilities = [[0.0 for _ in self.game_state.utilities[row]] for row in range(len(self.game_state.utilities))] 

        #loop until utility values converge
        for _ in range(CONVERGENCE_ITERATIONS):
            #calculate new utilities and save in temporary 2d array
            terminal_states = []
            if len(api.food(state)) == 1:
                terminal_states = terminal_states + api.food(state)
            for row in range(self.map_y):
                for col in range(self.map_x):
                    #if current pos not a wall, calculate new utility of pos
                    if (self.game_state.wall_bool[col][row] == False and ((col,row) not in terminal_states)):
                        converging_utilities[col][row] = self.setTransitionUtility(col, row)
            # copy over computed utility at coordinates (col, row) to game state
            self.game_state.utilities = converging_utilities
                    

        #update policies in actual map i.e. game_state
        for row in range(self.map_y):
           for col in range(self.map_x):
               #if current pos not a wall, update policy of pos
               if (self.game_state.wall_bool[col][row] == False):        
                    expected_utilities = []
                    expected_utilities.append(self.calculateUtility(self.game_state.utilities[col][row], self.game_state.utilities[col][row+1], 
                                                                    self.game_state.utilities[col-1][row], self.game_state.utilities[col+1][row])[1])
                    expected_utilities.append(self.calculateUtility(self.game_state.utilities[col][row], self.game_state.utilities[col][row-1], 
                                                                    self.game_state.utilities[col+1][row], self.game_state.utilities[col-1][row])[1])
                    expected_utilities.append(self.calculateUtility(self.game_state.utilities[col][row], self.game_state.utilities[col+1][row], 
                                                                    self.game_state.utilities[col][row+1], self.game_state.utilities[col][row-1])[1])
                    expected_utilities.append(self.calculateUtility(self.game_state.utilities[col][row], self.game_state.utilities[col-1][row], 
                                                                    self.game_state.utilities[col][row-1], self.game_state.utilities[col][row+1])[1])
                    expected_utilities.append(self.calculateUtility(self.game_state.utilities[col][row], self.game_state.utilities[col][row], 
                                                                    self.game_state.utilities[col][row], self.game_state.utilities[col][row])[1])
                    #find index of max in list
                    max_policy = expected_utilities.index(max(expected_utilities))
                    
                    #update policy in self.game_state 
                    self.game_state.transition_policies[col][row] = directions[max_policy]         
        
        # for row in range(self.map_y):
        #     row_values = []
        #     for col in range(self.map_x):
        #         row_values.append(self.game_state[col][row].utility)
        #     print(row_values)
        # print ' _ '*2*self.map_x

 
    #calculate and set utilities accoring to current policy in self.game_state
    def setTransitionUtility(self, col, row):
        if (self.game_state[col][row].transition_policy == Directions.NORTH):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row+1], self.game_state[col-1][row], self.game_state[col+1][row])[0]
        elif (self.game_state[col][row].transition_policy == Directions.SOUTH):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row-1], self.game_state[col-1][row], self.game_state[col+1][row])[0]
        elif (self.game_state[col][row].transition_policy == Directions.EAST):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col+1][row], self.game_state[col][row-1], self.game_state[col][row+1])[0]
        elif (self.game_state[col][row].transition_policy == Directions.WEST):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col-1][row], self.game_state[col][row-1], self.game_state[col][row+1])[0]
        else:
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row], self.game_state[col][row], self.game_state[col][row])[0]
 
 
    #method to calculate utility of moving from state s to s'
    def calculateUtility(self, current_pos, intended_move, alt_move_one, alt_move_two):
        wall_move = [m for m in [intended_move, alt_move_one, alt_move_two] if m.wall_bool == True]
        if wall_move:
            for move in wall_move:
                move = current_pos


        utility = current_pos + GAMMA_VALUE * (DETERMINISTIC_ACTION*intended_move + (NON_DETERMINISTIC_ACTION)*alt_move_one + 
                                                        (NON_DETERMINISTIC_ACTION)*alt_move_two)

        exp_utility = DETERMINISTIC_ACTION*intended_move + (NON_DETERMINISTIC_ACTION)*alt_move_one + (NON_DETERMINISTIC_ACTION)*alt_move_two
        
        return utility, exp_utility
 
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
    