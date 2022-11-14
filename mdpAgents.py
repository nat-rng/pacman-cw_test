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

GAMMA_VALUE = 1

#reward values
WALL_REWARD = 1
FOOD_REWARD = 3
GHOST_REWARD = -10
VULNERABLE_GHOST_REWARD = 3
EMPTYSPACE_REWARD = -5
CAPSULES_REWARD = 3

#nondeterministic probabilities
DETERMINISTICACTION = api.nonDeterministic
NONDETERMINISTICACTION = 1-DETERMINISTICACTION


class MapCoordinate:
    '''
    Class that signifies a single point 
    in a map
    '''
    def __init__(self, map_symbol, reward, policy_move, utility):
        self.map_symbol = map_symbol
        self.reward = reward
        self.policy_move = policy_move
        self.utility = utility
   
class MDPAgent(Agent):
    '''
    Agent that makes pacman traverse maze using the Markov Decision Problem
    '''

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        #get corners to generate map_width and map_height of map
        corners = api.corners(state)

        #find map_width and map_height
        self.map_width = self.getLayoutWidth(corners)
        self.map_height = self.getLayoutHeight(corners)

        #make 2d array size of map_width and map_height
        self.map_matrix = [[0 for row in range(self.map_height)] for col in range(self.map_width)] 

        self.initializeMapMatrix(state, self.map_matrix)
    
    def initializeMapMatrix(self, state, map_matrix):
        #generate imp lists     
        walls, ghosts, ghost_edible, capsules, foods = self.generateMapElementLists(state)
        
        #initialize 2d array with arbitrary values of MapCoordinate class
        for row in range(self.map_height):
            for col in range(self.map_width):
                if ((col, row) in walls):
                    map_matrix[col][row] = MapCoordinate('X', WALL_REWARD, Directions.STOP, 1.0)
                elif((col, row) in ghosts and ghost_edible==0):
                    map_matrix[col][row] = MapCoordinate('G', GHOST_REWARD, Directions.STOP, 1.0)
                elif((col, row) in ghosts and ghost_edible==1):
                    map_matrix[col][row] = MapCoordinate('E', VULNERABLE_GHOST_REWARD, Directions.STOP, 1.0)
                elif((col, row) in capsules):
                    map_matrix[col][row] = MapCoordinate('O', CAPSULES_REWARD, Directions.STOP, 1.0)
                elif((col, row) in foods):
                    map_matrix[col][row] = MapCoordinate('o', FOOD_REWARD, Directions.STOP, 1.0)
                else:
                    map_matrix[col][row] = MapCoordinate(' ', EMPTYSPACE_REWARD, Directions.STOP, 1.0)
        
    def generateMapElementLists(self, state):
        #generate lists of elements specified
        walls = api.walls(state)
        ghosts = api.ghosts(state)
        ghost_edible = api.ghostStates(state)[1]
        capsules = api.capsules(state)
        foods = api.food(state)
        return walls, ghosts, ghost_edible, capsules, foods

    #get height of maze  
    def getLayoutHeight(self, corners):
        map_height = -1
        for i in range(len(corners)):
            if corners[i][1] > map_height:
                map_height = corners[i][1]
        return map_height + 1

    #get width of maze
    def getLayoutWidth(self, corners):
        map_width = -1
        for i in range(len(corners)):
            if corners[i][0] > map_width:
                map_width = corners[i][0]
        return map_width + 1
    
    # This is what gets run in between multiple games
    def final(self, state):
        pass

    #update the map with new values of rewards and symbols
    def updateMap(self, state):
        #generate imp lists     
        walls, ghosts, ghost_edible, capsules, foods = self.generateMapElementLists(state)
        
        for row in range(self.map_height):
            for col in range(self.map_width):
                if ((col, row) in walls):
                    self.map_matrix[col][row].map_symbol = 'X'
                    self.map_matrix[col][row].reward = WALL_REWARD
                elif((col, row) in ghosts and ghost_edible==0):
                    self.map_matrix[col][row].map_symbol = 'G'
                    self.map_matrix[col][row].reward = GHOST_REWARD
                elif (((col+1, row) in ghosts ) or ((col, row+1) in ghosts) or ((col-1, row) in ghosts) or ((col, row-1) in ghosts) and ghost_edible==0):
                    self.map_matrix[col][row].map_symbol = 'g'
                    self.map_matrix[col][row].reward = GHOST_REWARD + 4
                elif (((col+1,row+1) in ghosts) or ((col+1,row-1) in ghosts) or ((col-1,row+1) in ghosts) or ((col-1,row-1) in ghosts) and ghost_edible==0):
                    self.map_matrix[col][row].map_symbol = 'g'
                    self.map_matrix[col][row].reward = GHOST_REWARD + 7
                elif((col, row) in ghosts and ghost_edible==1):
                    self.map_matrix[col][row].map_symbol = 'E'
                    self.map_matrix[col][row].reward = VULNERABLE_GHOST_REWARD
                elif (((col+1, row) in ghosts) or ((col, row+1) in ghosts) or ((col-1, row) in ghosts) or ((col, row-1) in ghosts) and ghost_edible==1):
                    self.map_matrix[col][row].map_symbol = 'e'
                    self.map_matrix[col][row].reward = VULNERABLE_GHOST_REWARD + 2
                elif (((col+1,row+1) in ghosts) or ((col+1,row-1) in ghosts) or ((col-1,row+1) in ghosts) or ((col-1,row-1) in ghosts) and ghost_edible==1):
                    self.map_matrix[col][row].map_symbol = 'e'
                    self.map_matrix[col][row].reward = VULNERABLE_GHOST_REWARD + 4
                elif((col, row) in capsules):
                    self.map_matrix[col][row].map_symbol = 'O'
                    self.map_matrix[col][row].reward = CAPSULES_REWARD
                elif((col, row) in foods):
                    self.map_matrix[col][row].map_symbol = 'o'
                    self.map_matrix[col][row].reward = FOOD_REWARD
                else:
                    self.map_matrix[col][row].map_symbol = ' '
                    self.map_matrix[col][row].reward = EMPTYSPACE_REWARD

        self.map_matrix[api.whereAmI(state)[0]][api.whereAmI(state)[1]].map_symbol = 'P'              

    #method for calculating updating all the utilities and policies in self.map_matrix        
    def calculateUtilitiesAndPolicies(self, state):
        #list to choose a move from based on calculation from the method updatePolicy
        directions_list = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST, Directions.STOP]
        
        #make copy of utilites
        temp_map_utilities = [[0 for row in range(self.map_height)] for col in range(self.map_width)] 

        #loop till near convergence 
        for i in range(50):
            
            #calculate new utilities and save in temporary 2d array
            for row in range(self.map_height):
                for col in range(self.map_width):
                    #if current pos not a wall, calculate new utility of pos
                    if (not (self.map_matrix[col][row].map_symbol == 'X')):    
                        temp_map_utilities[col][row] = self.getNewUtility(col, row)
            
            #copy calculated utilities to map_matrix
            for row in range(self.map_height):
                for col in range(self.map_width):
                    self.map_matrix[col][row].utility = temp_map_utilities[col][row]

        #update policies in actual map i.e. map_matrix
        for row in range(self.map_height):
           for col in range(self.map_width):
               #if current pos not a wall, update policy of pos
               if (not (self.map_matrix[col][row].map_symbol == 'X')):        
                   self.updatePolicy(col, row, directions_list)           

    #method to update policy in self.map_matrix
    def updatePolicy(self, col, row, directions_list):
        #calculate new policy to be used in the next iteration for self.map_matrix
        expected_utilities = []
        expected_utilities.append(self.calculateExpectedUtility(self.map_matrix[col][row], self.map_matrix[col][row+1], self.map_matrix[col-1][row], self.map_matrix[col+1][row], self.map_matrix[col][row-1]))
        expected_utilities.append(self.calculateExpectedUtility(self.map_matrix[col][row], self.map_matrix[col][row-1], self.map_matrix[col+1][row], self.map_matrix[col-1][row], self.map_matrix[col][row+1]))
        expected_utilities.append(self.calculateExpectedUtility(self.map_matrix[col][row], self.map_matrix[col+1][row], self.map_matrix[col][row+1], self.map_matrix[col][row-1], self.map_matrix[col-1][row]))
        expected_utilities.append(self.calculateExpectedUtility(self.map_matrix[col][row], self.map_matrix[col-1][row], self.map_matrix[col][row-1], self.map_matrix[col][row+1], self.map_matrix[col+1][row]))
        expected_utilities.append(self.calculateExpectedUtility(self.map_matrix[col][row], self.map_matrix[col][row], self.map_matrix[col][row], self.map_matrix[col][row], self.map_matrix[col][row]))

        #find index of max in list
        new_policy_index = self.findMaxIndex(expected_utilities)
        
        #update policy in self.map_matrix 
        self.map_matrix[col][row].policy_move = directions_list[new_policy_index]

    #calculate and set utilities accoring to current policy in self.map_matrix
    def getNewUtility(self, col, row):
        if (self.map_matrix[col][row].policy_move == Directions.NORTH):
            return self.calculateUtility(self.map_matrix[col][row], self.map_matrix[col][row+1], self.map_matrix[col-1][row], self.map_matrix[col+1][row], self.map_matrix[col][row-1])
        elif (self.map_matrix[col][row].policy_move == Directions.SOUTH):
            return self.calculateUtility(self.map_matrix[col][row], self.map_matrix[col][row-1], self.map_matrix[col+1][row], self.map_matrix[col-1][row], self.map_matrix[col][row+1])
        elif (self.map_matrix[col][row].policy_move == Directions.EAST):
            return self.calculateUtility(self.map_matrix[col][row], self.map_matrix[col+1][row], self.map_matrix[col][row+1], self.map_matrix[col][row-1], self.map_matrix[col-1][row])
        elif (self.map_matrix[col][row].policy_move == Directions.WEST):
            return self.calculateUtility(self.map_matrix[col][row], self.map_matrix[col-1][row], self.map_matrix[col][row-1], self.map_matrix[col][row+1], self.map_matrix[col+1][row])
        else:
            return self.calculateUtility(self.map_matrix[col][row], self.map_matrix[col][row], self.map_matrix[col][row], self.map_matrix[col][row],self.map_matrix[col][row])
    
    #method to calculate maximum index of list
    def findMaxIndex(self, list):
        return list.index(max(list))

    #method to calculate utility of moving from state s to moving to s'
    def calculateUtility(self, map_coordinate, map_coordinate_forward, map_coordinate_left, map_coordinate_right, map_coordinate_back):
        if map_coordinate_forward.map_symbol == 'X':
            map_coordinate_forward = map_coordinate

        if map_coordinate_left.map_symbol == 'X':
            map_coordinate_left = map_coordinate

        if map_coordinate_right.map_symbol == 'X':
            map_coordinate_right = map_coordinate
            
        if map_coordinate_back.map_symbol == 'X':
            map_coordinate_back = map_coordinate

        utility = map_coordinate.reward + GAMMA_VALUE * (DETERMINISTICACTION*map_coordinate_forward.utility + (NONDETERMINISTICACTION/3)*map_coordinate_left.utility + 
                                                        (NONDETERMINISTICACTION/3)*map_coordinate_right.utility + (NONDETERMINISTICACTION/3)*map_coordinate_back.utility)
        return utility

    #method for calculating expected utility of moving from state s to s'
    def calculateExpectedUtility(self, map_coordinate, map_coordinate_forward, map_coordinate_left, map_coordinate_right, map_coordinate_back):
        if map_coordinate_forward.map_symbol == 'X':
            map_coordinate_forward = map_coordinate

        if map_coordinate_left.map_symbol == 'X':
            map_coordinate_left = map_coordinate

        if map_coordinate_right.map_symbol == 'X':
            map_coordinate_right = map_coordinate

        if map_coordinate_back.map_symbol == 'X':
            map_coordinate_back = map_coordinate

        exp_utility = DETERMINISTICACTION*map_coordinate_forward.utility + (NONDETERMINISTICACTION/3)*map_coordinate_left.utility + (NONDETERMINISTICACTION/3)*map_coordinate_right.utility + (NONDETERMINISTICACTION/3)*map_coordinate_back.utility
        return exp_utility

    def getAction(self, state):
        # update map 
        self.updateMap(state)
        
        #calculate new utilities and policies and save in self.map_matrix
        self.calculateUtilitiesAndPolicies(state)

        #get all legal actions at current pacman pos
        legal = api.legalActions(state)
        
        #get pacman pos
        pacman_pos = api.whereAmI(state)
        
        #get the policy saved on pacmans current pos
        move_to_make = self.map_matrix[pacman_pos[0]][pacman_pos[1]].policy_move

        #make move
        return api.makeMove(move_to_make, legal)
    