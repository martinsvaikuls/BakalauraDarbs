import random
import math
import csv
import ast
import numpy as np

import datetime
import time

from copy import deepcopy

from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import StrEnum


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

class NodeType(StrEnum):
    TECH = "tech"
    TASK = "task"
    DEPOT = "depot"
    SHOP = "shop"

@dataclass(frozen=True, slots=True)
class Route_Node:
    node_type: NodeType
    id: int

class Node_Distances: 
    def __init__(self, row):
        self.distances: Dict[Tuple[Route_Node, Route_Node], float] = {}

    def get_distance(self, a: Route_Node, b: Route_Node):
        if (a, b) not in self.distances:
            self.update_distance(a,b)

        return self.distances[(a, b)]

    def update_distance():
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

class Solution: 
    def __init__(self, technicians):
        self.tech_map = {t.id: t for t in technicians}
        self.master_ids = {t.id: t.master_id for t in technicians} 

        self.routes = {t.id: [] for t in technicians} 
        self.changedRoute = {t.id: False for t in technicians} # checks if there is need to recalculate costs and incomes
        
        self.monetaryCost = {t.id: 0.0 for t in technicians} #total cost per technician
        self.pathCost = {t.id: 0.0 for t in technicians} #driving (cost for path)
        self.timeCost = {t.id: 0.0 for t in technicians} #work (both for driving and work)
        self.weatherCost = {t.id: 0.0 for t in technicians} #security (total cost for technician in all types of weather)
        self.income = {t.id: 0.0 for t in technicians} #total income per tasks for technician

        self.totalMonetaryCost = 0.0
        self.totalPathCost = 0.0
        self.totalTimeCost = 0.0
        self.totalWeatherCost = 0.0
        self.totalIncome = 0.0


        self.workHourCost = 20
        self.drivingHundredKMCost = 2.00*6
        self.drivingSpeedHr = 60
        self.drivingHourCost = self.drivingHundredKMCost*60/100

    
    def calculateMonetaryCostForTechnician(self):
        changedRoute = self.changedRoute

        for tech_id, cr in changedRoute:
            if cr:
                cost = 0
                cost += self.pathCost[tech_id]
                cost += self.timeCost[tech_id]
                cost += self.weatherCost[tech_id]
                
                self.monetaryCost[tech_id] = cost

        
    def calculatePathCost(self, distances):
        routes = self.routes
        changedRoute = self.changedRoute

        for tech_id, cr in changedRoute:
            if cr:
                current_tech_position = Route_Node(NodeType.TECH, tech_id)
                cost = 0.0
                for technician_id, route in routes:
                    for node in route:
                        next_route_position = node
                        cost += distances.get_distance(current_tech_position, next_route_position)
                        current_tech_position = next_route_position
                self.pathCost[tech_id] = cost * self.drivingHourCost


    def calculateTimeCost(self, tasks):
        routes = self.routes
        changedRoute = self.changedRoute

        for tech_id, cr in changedRoute:
            if cr:
                duration_work = 0.0
                cost_drive = 0.0
                for technician_id, route in routes:
                    for node in route:
                        duration_work += tasks[node.id].duration

                cost_work = duration_work * self.workHourCost
                cost_drive = (self.pathCost[tech_id] / self.drivingHourCost) * self.workHourCost
                self.timeCost[tech_id] = cost_drive + cost_work


    def calculateWeatherCost(self):
        pass


    def calculateIncome(self, tasks):
        routes = self.routes
        changedRoute = self.changedRoute
        for tech_id, cr in changedRoute:
            if cr:
                incomeTech = 0.0
   
                for technician_id, route in routes:
                    for node in route:
                        incomeTech += tasks[node.id].income

                self.income[tech_id] = incomeTech
                

    def updateTotals(self):
        pathCost = 0
        timeCost = 0
        weatherCost = 0
        income = 0

        changedRoute = self.changedRoute 
        for tech_id, cr in changedRoute:
            pathCost += self.pathCost[tech_id]
            timeCost += self.timeCost[tech_id]
            weatherCost += self.weatherCost[tech_id]
            income += self.income[tech_id]

        self.totalMonetaryCost = pathCost + timeCost + weatherCost
        self.totalPathCost = pathCost
        self.totalTimeCost = timeCost
        self.totalWeatherCost = weatherCost
        self.totalIncome = income


    def __str__(self, row):
        pass
    """

    """     

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
