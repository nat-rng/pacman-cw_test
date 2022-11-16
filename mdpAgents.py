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

GAMMA_VALUE = 0.80
CONVERGENCE_ITERATIONS = 50

#reward values
WALL_REWARD = 0
FOOD_REWARD = 10
GHOST_REWARD = -18
VULNERABLE_GHOST_REWARD = 6
EMPTY_REWARD = -1
CAPSULES_REWARD = 4

DISTANCE_MULTIPLIER = 2.2 #2.2
GHOST_RADIUS = 2.1 #2.1
#nondeterministic probabilities
DETERMINISTIC_ACTION = api.nonDeterministic
NON_DETERMINISTIC_ACTION = (1-DETERMINISTIC_ACTION)/2
NO_OF_RUNS = 0


class Coordinates():
    '''
    Sets atrtibutes for point on the map if it is a wall, reward, policy and utility
    '''
    def __init__(self, wall_bool, reward, policy=Directions.STOP, utility=0.0):
        self.wall_bool = wall_bool
        self.reward = reward
        self.transition_policy = policy
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

        #Code was modified from the provided mapAgents.py file from PRactical 5    
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
        walls = api.walls(state)
        ghosts = api.ghosts(state)
        capsules = api.capsules(state)
        foods = api.food(state)
        
        #initialize 2d array with arbitrary values of MapCoordinate class
        for wall in walls:
            self.game_state[wall[0]][wall[1]] = Coordinates(True, WALL_REWARD)

        for capsule in capsules:
            self.game_state[capsule[0]][capsule[1]] = Coordinates(False, CAPSULES_REWARD)

        for food in foods:
            self.game_state[food[0]][food[1]] = Coordinates(False, FOOD_REWARD)

        for ghost in ghosts:
            self.game_state[ghost[0]][ghost[1]] = Coordinates(False, GHOST_REWARD)

 
    # This is what gets run in between multiple games
    def final(self, state):
        global NO_OF_RUNS 
        global FOOD_REWARD
        NO_OF_RUNS += 1
        # if NO_OF_RUNS % 25 == 0:
        #     FOOD_REWARD += 1
        print "Looks like the game just ended!"
        print "This was run number: " + str(NO_OF_RUNS)
 
    #update the map with new values of rewards and symbols
    def updateRewards(self, state):     
        walls = api.walls(state)
        ghost_edible = api.ghostStates(state)
        capsules = api.capsules(state)
        foods = api.food(state)
        close_to_ghost = self.ghostRadius(state, GHOST_RADIUS)

        for capsule in capsules:
            self.game_state[capsule[0]][capsule[1]].reward = CAPSULES_REWARD

        self.setFoodReward(state, foods)

        for area in close_to_ghost[0]:
            if((area[0], area[1]) not in walls):
                index = close_to_ghost[0].index((area[0], area[1]))
                manhatten_distance = close_to_ghost[1][index]
                if len(ghost_edible) < 2:
                    self.game_state[area[0]][area[1]].reward = GHOST_REWARD + DISTANCE_MULTIPLIER*manhatten_distance

                for i in range(len(ghost_edible)):
                    if ghost_edible[i][1] == 1:
                        self.game_state[area[0]][area[1]].reward = VULNERABLE_GHOST_REWARD - DISTANCE_MULTIPLIER*manhatten_distance
                    else:
                        self.game_state[area[0]][area[1]].reward = GHOST_REWARD + DISTANCE_MULTIPLIER*manhatten_distance
        
        for row in range(self.map_y):
            for col in range(self.map_x):
                excluded_coords = [walls + capsules + foods + close_to_ghost[0]]
                if (col, row) not in set().union(*excluded_coords):
                    self.game_state[col][row].reward = EMPTY_REWARD

        # for row in range(self.map_y):
        #     row_values = []
        #     for col in range(self.map_x):
        #         row_values.append(self.game_state[col][row].reward)
        #     print(row_values)
    def setFoodReward(self, state, foods):
        walls = api.walls(state)
        nearby_walls = []
        for food in foods:
            for i in range(len(walls)):
                if util.manhattanDistance(food,walls[i]) <= 1:
                    nearby_walls.append(walls[i])

                self.game_state[food[0]][food[1]].reward = FOOD_REWARD / (1 + len(nearby_walls))
    
    def ghostRadius(self, state, limit):
        corners = api.corners(state)
        self.map_x = self.getLayoutWidth(corners)
        self.map_y = self.getLayoutHeight(corners)
        grid = [(i,j) for i in range(self.map_x) for j in range(self.map_y)]
        ghosts = api.ghosts(state)
        withinLimit = set()
        
        for ghost in ghosts:
            for i in range(len(grid)):
                manhattanDistance = util.manhattanDistance(ghost,grid[i])
                if manhattanDistance <= limit:
                    withinLimit.add((grid[i],manhattanDistance))

        dual_list = list(map(list, zip(*withinLimit)))
        return dual_list
 
    #method for calculating updating all the utilities and policies in self.game_state        
    def updateUtilitiesAndTransitions(self, state):
        #list to choose a move from based on calculation from the method updatePolicy
        directions_list = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST, Directions.STOP]
        
        #make copy of utilites
        converging_utilities = [[0.0 for _ in range(self.map_y)] for _ in range(self.map_x)] 

        #loop till near convergence 
        for _ in range(CONVERGENCE_ITERATIONS):
            
            #calculate new utilities and save in temporary 2d array
            for row in range(self.map_y):
                for col in range(self.map_x):
                    #if current pos not a wall, calculate new utility of pos
                    if (not (self.game_state[col][row].wall_bool == True)):    
                        converging_utilities[col][row] = self.getNewUtility(col, row)
            
            #copy calculated utilities to game_state
            for row in range(self.map_y):
                for col in range(self.map_x):
                    self.game_state[col][row].utility = converging_utilities[col][row]

        #update policies in actual map i.e. game_state
        for row in range(self.map_y):
           for col in range(self.map_x):
               #if current pos not a wall, update policy of pos
               if (not (self.game_state[col][row].wall_bool == True)):        
                   self.updatePolicy(col, row, directions_list)           
 
    #method to update policy in self.game_state
    def updatePolicy(self, col, row, directions_list):
        #calculate new policy to be used in the next iteration for self.game_state
        expected_utilities = []
        expected_utilities.append(self.calculateExpectedUtility(self.game_state[col][row], self.game_state[col][row+1], self.game_state[col-1][row], self.game_state[col+1][row]))
        expected_utilities.append(self.calculateExpectedUtility(self.game_state[col][row], self.game_state[col][row-1], self.game_state[col+1][row], self.game_state[col-1][row]))
        expected_utilities.append(self.calculateExpectedUtility(self.game_state[col][row], self.game_state[col+1][row], self.game_state[col][row+1], self.game_state[col][row-1]))
        expected_utilities.append(self.calculateExpectedUtility(self.game_state[col][row], self.game_state[col-1][row], self.game_state[col][row-1], self.game_state[col][row+1]))
        expected_utilities.append(self.calculateExpectedUtility(self.game_state[col][row], self.game_state[col-1][row], self.game_state[col][row], self.game_state[col][row]))
        #find index of max in list
        new_policy_index = self.findMaxIndex(expected_utilities)
        
        #update policy in self.game_state 
        self.game_state[col][row].transition_policy = directions_list[new_policy_index]
 
    #calculate and set utilities accoring to current policy in self.game_state
    def getNewUtility(self, col, row):
        if (self.game_state[col][row].transition_policy == Directions.NORTH):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row+1], self.game_state[col-1][row], self.game_state[col+1][row])
        elif (self.game_state[col][row].transition_policy == Directions.SOUTH):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row-1], self.game_state[col-1][row], self.game_state[col+1][row])
        elif (self.game_state[col][row].transition_policy == Directions.EAST):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col+1][row], self.game_state[col][row-1], self.game_state[col][row+1])
        elif (self.game_state[col][row].transition_policy == Directions.WEST):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col-1][row], self.game_state[col][row-1], self.game_state[col][row+1])
        else:
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row], self.game_state[col][row], self.game_state[col][row])
 
    #method to calculate maximum index of list
    def findMaxIndex(self, list):
        return list.index(max(list))
 
    #method to calculate utility of moving from state s to moving to s'
    def calculateUtility(self, current_pos, intended_move, alt_move_one, alt_move_two):
        if intended_move.wall_bool == True:
            intended_move = current_pos

        if alt_move_one.wall_bool == True:
            alt_move_one = current_pos

        if alt_move_two.wall_bool == True:
            alt_move_two = current_pos

        utility = current_pos.reward + GAMMA_VALUE * (DETERMINISTIC_ACTION*intended_move.utility + (NON_DETERMINISTIC_ACTION)*alt_move_one.utility + 
                                                        (NON_DETERMINISTIC_ACTION)*alt_move_two.utility)
        return utility
 
    #method for calculating expected utility of moving from state s to s'
    def calculateExpectedUtility(self, current_pos, intended_move, alt_move_one, alt_move_two):
        if intended_move.wall_bool == True:
            intended_move = current_pos

        if alt_move_one.wall_bool == True:
            alt_move_one = current_pos

        if alt_move_two.wall_bool == True:
            alt_move_two = current_pos

        exp_utility = DETERMINISTIC_ACTION*intended_move.utility + (NON_DETERMINISTIC_ACTION)*alt_move_one.utility + (NON_DETERMINISTIC_ACTION)*alt_move_two.utility
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
    