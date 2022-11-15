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

GAMMA_VALUE = 0.9
CONVERGENCE_ITERATIONS = 30

#reward values
WALL_REWARD = 0
FOOD_REWARD = 15
GHOST_REWARD = -80
VULNERABLE_GHOST_REWARD = 50
EMPTYSPACE_REWARD = -50
CAPSULES_REWARD = 10

#nondeterministic probabilities
DETERMINISTIC_ACTION = api.nonDeterministic
NON_DETERMINISTIC_ACTION = (1-DETERMINISTIC_ACTION)/2


class Coordinates():
    '''
    Sets atrtibutes for point on the map if it is a wall, reward, policy and utility
    '''
    def __init__(self, wall_bool, reward, policy=Directions.STOP, utility=0.0):
        self.wall_bool = wall_bool
        self.reward = reward
        self.policy = policy
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

        #make 2d array size of map_x and map_y
        self.game_state = [[0 for _ in range(self.map_y)] for _ in range(self.map_x)] 

        self.initializeMapStates(state, self.game_state)
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
    
    def initializeMapStates(self, state, game_state):
        #generate imp lists     
        walls = api.walls(state)
        ghosts = api.ghosts(state)
        capsules = api.capsules(state)
        foods = api.food(state)
        
        #initialize 2d array with arbitrary values of MapCoordinate class
        for row in range(self.map_y):
            for col in range(self.map_x):
                if ((col, row) in walls):
                    game_state[col][row] = Coordinates(True, WALL_REWARD)
                elif((col, row) in ghosts):
                    game_state[col][row] = Coordinates(False, GHOST_REWARD)
                elif((col, row) in capsules):
                    game_state[col][row] = Coordinates(False, CAPSULES_REWARD)
                elif((col, row) in foods):
                    game_state[col][row] = Coordinates(False, FOOD_REWARD)
                else:
                    game_state[col][row] = Coordinates(False, EMPTYSPACE_REWARD)
    
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

    #update the map with new values of rewards and symbols
    def updateRewards(self, state):
        #generate imp lists     
        walls = api.walls(state)
        ghosts = api.ghosts(state)
        ghost_edible = api.ghostStates(state)
        capsules = api.capsules(state)
        foods = api.food(state)
        
        for row in range(self.map_y):
            for col in range(self.map_x):
                if ((col, row) in walls):
                    self.game_state[col][row].wall_bool = True
                    self.game_state[col][row].reward = WALL_REWARD
                elif((col, row) in ghosts and ghost_edible==0):
                    self.game_state[col][row].reward = GHOST_REWARD
                elif (((col+1, row) in ghosts ) or ((col, row+1) in ghosts) or ((col-1, row) in ghosts) or ((col, row-1) in ghosts)):
                    self.game_state[col][row].reward = GHOST_REWARD - 15
                elif (((col+1,row+1) in ghosts) or ((col+1,row-1) in ghosts) or ((col-1,row+1) in ghosts) or ((col-1,row-1) in ghosts)):
                    self.game_state[col][row].reward = GHOST_REWARD - 30
                elif(((col, row),1) in ghost_edible):
                    self.game_state[col][row].reward = VULNERABLE_GHOST_REWARD
                elif ((((col+1, row),1) in ghost_edible) or (((col, row+1),1) in ghost_edible) or (((col-1, row),1) in ghost_edible) or (((col, row-1),1) in ghost_edible)):
                    self.game_state[col][row].reward = VULNERABLE_GHOST_REWARD + 10
                elif ((((col+1,row+1),1) in ghost_edible) or (((col+1,row-1),1) in ghost_edible) or (((col-1,row+1),1) in ghost_edible) or (((col-1,row-1),1) in ghost_edible)):
                    self.game_state[col][row].reward = VULNERABLE_GHOST_REWARD + 15
                elif((col, row) in capsules):
                    self.game_state[col][row].reward = CAPSULES_REWARD
                elif((col, row) in foods):
                    self.game_state[col][row].reward = FOOD_REWARD
                else:
                    self.game_state[col][row].reward = EMPTYSPACE_REWARD
            

    #method for calculating updating all the utilities and policies in self.game_state        
    def calculateUtilitiesAndPolicies(self, state):
        #list to choose a move from based on calculation from the method updatePolicy
        directions_list = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        
        #make copy of utilites
        temp_map_utilities = [[0 for _ in range(self.map_y)] for _ in range(self.map_x)] 

        #loop till near convergence 
        for _ in range(CONVERGENCE_ITERATIONS):
            
            #calculate new utilities and save in temporary 2d array
            for row in range(self.map_y):
                for col in range(self.map_x):
                    #if current pos not a wall, calculate new utility of pos
                    if (not (self.game_state[col][row].wall_bool == True)):    
                        temp_map_utilities[col][row] = self.getNewUtility(col, row)
            
            #copy calculated utilities to game_state
            for row in range(self.map_y):
                for col in range(self.map_x):
                    self.game_state[col][row].utility = temp_map_utilities[col][row]

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

        #find index of max in list
        new_policy_index = self.findMaxIndex(expected_utilities)
        
        #update policy in self.game_state 
        self.game_state[col][row].policy = directions_list[new_policy_index]

    #calculate and set utilities accoring to current policy in self.game_state
    def getNewUtility(self, col, row):
        if (self.game_state[col][row].policy == Directions.NORTH):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row+1], self.game_state[col-1][row], self.game_state[col+1][row])
        elif (self.game_state[col][row].policy == Directions.SOUTH):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row-1], self.game_state[col+1][row], self.game_state[col-1][row])
        elif (self.game_state[col][row].policy == Directions.EAST):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col+1][row], self.game_state[col][row+1], self.game_state[col][row-1])
        elif (self.game_state[col][row].policy == Directions.WEST):
            return self.calculateUtility(self.game_state[col][row], self.game_state[col-1][row], self.game_state[col][row-1], self.game_state[col][row+1])
        else:
            return self.calculateUtility(self.game_state[col][row], self.game_state[col][row], self.game_state[col][row], self.game_state[col][row])
    
    #method to calculate maximum index of list
    def findMaxIndex(self, list):
        return list.index(max(list))

    #method to calculate utility of moving from state s to moving to s'
    def calculateUtility(self, coordinates, intended_move, alt_move_one, alt_move_two):
        if intended_move.wall_bool == True:
            intended_move = coordinates

        if alt_move_one.wall_bool == True:
            alt_move_one = coordinates

        if alt_move_two.wall_bool == True:
            alt_move_two = coordinates

        utility = coordinates.reward + GAMMA_VALUE * (DETERMINISTIC_ACTION*intended_move.utility + (NON_DETERMINISTIC_ACTION)*alt_move_one.utility + 
                                                        (NON_DETERMINISTIC_ACTION)*alt_move_two.utility)
        return utility

    #method for calculating expected utility of moving from state s to s'
    def calculateExpectedUtility(self, coordinates, intended_move, alt_move_one, alt_move_two):
        if intended_move.wall_bool == True:
            intended_move = coordinates

        if alt_move_one.wall_bool == True:
            alt_move_one = coordinates

        if alt_move_two.wall_bool == True:
            alt_move_two = coordinates

        exp_utility = DETERMINISTIC_ACTION*intended_move.utility + (NON_DETERMINISTIC_ACTION)*alt_move_one.utility + (NON_DETERMINISTIC_ACTION)*alt_move_two.utility
        return exp_utility

    def getAction(self, state):
        # update map 
        self.updateRewards(state)
        
        #calculate new utilities and policies and save in self.game_state
        self.calculateUtilitiesAndPolicies(state)

        #get all legal actions at current pacman pos
        legal = api.legalActions(state)
        
        #get pacman pos
        pacman_pos = api.whereAmI(state)
        
        #get the policy saved on pacmans current pos
        move_to_make = self.game_state[pacman_pos[0]][pacman_pos[1]].policy

        #make move
        return api.makeMove(move_to_make, legal)
    