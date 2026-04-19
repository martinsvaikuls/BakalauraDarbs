import random
import math
import csv
import ast
from copy import deepcopy
import datetime
import time
import numpy as np


class Tasks: 
    def __init__(self, row):
        self.id = int(row["id"])
        self.skills = set(ast.literal_eval(row["skills"]))
        
        self.resources = set(ast.literal_eval(row["resources"]))

        self.priority = int(row["priority"])
        self.start_tw = (datetime.datetime.fromisoformat(str(row["start_tw"])))
        self.end_tw = (datetime.datetime.fromisoformat(str(row["end_tw"])))
        self.duration = int(row["duration"])
        self.created = int(row["created"])

        self.lat = float(row["home_lat"])
        self.long = float(row["home_long"])

    def __str__(self, row):
        pass

class Technicians: 
    def __init__(self, row):
        self.id = int(row["id"])
        self.master_id = int(row["master_id"])
        self.skills = set(ast.literal_eval(row["skills"]))

        self.resources = set(ast.literal_eval(row["resources"]))

        self.start_tw = (datetime.datetime.fromisoformat(str(row["start_tw"])))
        self.end_tw = (datetime.datetime.fromisoformat(str(row["end_tw"])))

        self.lat = float(row["home_lat"])
        self.long = float(row["home_long"])
        self.home = self.lat, self.long

        self.created = int(row["created"])
        self.new_start_tw = 0

    def __str__(self, row):
        pass

class Solution: 
    def __init__(self, technicians):
        self.tech_map = {t.id: t for t in technicians}
        self.routes = {t.id: [] for t in technicians} 
        self.master_ids = {t.id: t.master_id for t in technicians} 
        self.monetaryCost = {t.id: [] for t in technicians} 
        self.pathCost = {t.id: [] for t in technicians} #driving
        self.timeCost = {t.id: [] for t in technicians} #work
        self.weatherCost = {t.id: [] for t in technicians} #security
        self.income = {t.id: [] for t in technicians} 
        
        self.totalCost = 0.0
        self.pathCost = 0.0
        self.timeCost = 0.0
        self.weatherCost = 0.0
        self.income = 0.0

        self.workHourCost = 20
        self.drivingHundredKMCost = 2.00*6
        self.drivingSpeedHr = 60
        self.drivingHourCost = self.drivingHundredKMCost*60/100

    def calculateMonetaryCost(self):
        #driving
        #penalties
        #work
        pathCost = deepcopy(self.pathCost)
        timeCost = deepcopy(self.timeCost)
        weatherCost = deepcopy(self.weatherCost)
        

        
        cost = 0
        



        pass
    def calculatePathCost(self):
        tech_map = deepcopy(self.tech_map)
        routes = deepcopy(self.routes)

        pass
    def calculateTimeCost(self):
        tech_map = deepcopy(self.tech_map)
        routes = deepcopy(self.routes)



        pass
    def calculateWeatherCost(self):
        pass
    def calculateIncome(self):
        pass                
        
    def __str__(self, row):
        pass

class Operators: 
    def __init__(self, row):
        self.destroy = Destroy_Operator()
        self.repair = Repair_Operator()
        
        self.chosen_destroy = 0
        self.chosen_repair = 0

        self.weights_destroy = []
        self.weights_repair = []

        self.score = 0
               
    def roulette():
        pass
    def destroy():
        pass
    def repair():
        pass
    def renewWeights():
        pass
    def updateScore():
        pass         

    def __str__(self, row):
        pass

class Destroy_Operator: 
    def __init__(self, row):
        pass
    
    def random():
        pass
    def route():
        pass
    def critical():
        pass
    def shaw():
        pass
    def skill():
        pass
    def type():
        pass  
        
    def __str__(self, row):
        pass

class Repair_Operator: 
    def __init__(self, row):
        pass
    def greedy():
        pass
    def regret():
        pass
    def random():
        pass
    def __str__(self, row):
        pass

class Node_Distances: 
    def __init__(self, row):
        pass
    def getDistance():
        pass
    def update():
        pass
    def __str__(self, row):
        pass

class Weather: 
    def __init__(self, row):
        self.average = 160.932
        self.sunshine = 197.624
        self.rain = 226.109
        self.snow = 446.264
        self.wind = 163.668
        self.weatherType = 1
        
        
    def getWeather():
        pass
    def getPenalty(self, weatherType):
        if weatherType == 1:
            return self.average
        elif weatherType == 1:
            return self.average
    
    def __str__(self, row):
        pass

class ALNS_ALgorithm: 
    def __init__(self, row):
        self.simulatedAnnealing_temperature = 100.0
        self.best_solution = Solution()
        self.operators = Operators()

    def selectOperators():
        pass
    def generateNewSolution():
        pass
    def acceptSimulatedAnnealingFunction():
        pass
    def updateWeights():
        pass
    def initialize():
        pass

    def __str__(self, row):
        pass
