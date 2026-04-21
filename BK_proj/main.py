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

    
    def updateCosts_Income(self, distances, tasks):
        routes = self.routes
        changedRoute = self.changedRoute

        totalPathCost = 0.0
        totalTimeCost = 0.0
        totalWeatherCost = 0.0
        totalIncome = 0.0

        for tech_id, cr in changedRoute.items():
            if cr:
                current_tech_position = Route_Node(NodeType.TECH, tech_id)
                cost_monetary = 0.0

                duration_work = 0.0
                cost_drive = 0.0

                weatherCost = 0.0


                incomeTech = 0.0

                route = routes[tech_id]
                ##for technician_id, route in routes.items():
                for node in route:
                    next_route_position = node
                    cost_drive += distances.get_distance(current_tech_position, next_route_position)
                    current_tech_position = next_route_position

                    ### weather
                    ######

                    if node.node_type == NodeType.TASK:
                        duration_work += tasks[node.id].duration
                        incomeTech += tasks[node.id].income


                self.pathCost[tech_id] = cost_drive * self.drivingHourCost                  

                cost_work = duration_work * self.workHourCost
                cost_drive = (self.pathCost[tech_id] / self.drivingHourCost) * self.workHourCost
                self.timeCost[tech_id] = cost_drive + cost_work

                ######### WEATHER

                self.weatherCost[tech_id] = weatherCost
                ################


                cost_monetary += self.pathCost[tech_id]
                cost_monetary += self.timeCost[tech_id]
                cost_monetary += self.weatherCost[tech_id]
                
                self.monetaryCost[tech_id] = cost_monetary

                self.income[tech_id] = incomeTech

                self.changedRoute[tech_id] = False

            
            totalPathCost += self.pathCost[tech_id]
            totalTimeCost += self.timeCost[tech_id]
            totalWeatherCost += self.weatherCost[tech_id]
            totalIncome += self.income[tech_id]
        
        self.totalMonetaryCost = totalPathCost + totalTimeCost + totalWeatherCost
        self.totalPathCost = totalPathCost
        self.totalTimeCost = totalTimeCost
        self.totalWeatherCost = totalWeatherCost
        self.totalIncome = totalIncome

    """
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
    """

    def __str__(self, row):
        pass
    """

    """     

class Operators: 
    def __init__(self, row):
        self.destroy_ops = Destroy_Operator()
        self.repair_ops = Repair_Operator()
        
        self.chosen_destroy = 0
        self.chosen_repair = 0

        self.weights_destroy = [1.0] * 6
        self.weights_repair = [1.0] * 3

        self.score = 0
        self.reaction = 0.1
               
    def roulette(self):
        total_destroy = sum(self.weights_destroy)
        total_repair = sum(self.weights_repair)

        pick_destroy = random.uniform(0, total_destroy)
        pick_repair = random.uniform(0, total_repair)


        current = 0.0
        for operator, weight in enumerate(self.weights_destroy):
            current += weight
            if current >= pick_destroy:
                self.chosen_destroy = operator
                break

        current = 0.0
        for operator, weight in enumerate(self.weights_repair):
            current += weight
            if current >= pick_repair:
                self.chosen_repair = operator
                break
    

    def destroy(self, solution):
        match self.chosen_destroy:
            case 0:
                return self.destroy_ops.random(solution)
            case 1:
                return self.destroy_ops.route(solution)
            case 2:
                return self.destroy_ops.critical(solution)
            case 3:
                return self.destroy_ops.shaw(solution)
            case 4:
                return self.destroy_ops.skill(solution)
            case 5:
                return self.destroy_ops.type(solution)
            

    def repair(self, solution):
        match self.chosen_repair:
            case 0:
                return self.repair_ops.greedy(solution)
            case 1:
                return self.repair_ops.regret(solution)
            case 2:
                return self.repair_ops.random(solution)


    def renew_weights(self):
        self.weights_destroy[self.chosen_destroy] = (1.0 - self.reaction) * self.weights_destroy[self.chosen_destroy] + self.reaction * self.score
        self.weights_repair[self.chosen_repair] = (1.0 - self.reaction) * self.weights_repair[self.chosen_repair] + self.reaction * self.score
        
    def updateScore(self,new_score):
        self.score = new_score

    def __str__(self, row):
        pass

class Destroy_Operator: 
    def __init__(self, row):
        pass
    
    def random(solution, unassigned_tasks): #k should be 10% of all nodes (but why?)
        new_solution = deepcopy(solution)
        all_nodes = [
        (tech_id, node)
        for tech_id, route in solution.routes.items()
        for node in route
        if node.node_type == NodeType.TASK
        ]

        k = int(max(1, len(all_nodes) * 0.1))
        removed_nodes = random.sample(all_nodes, k)

        for tech_id, node in removed_nodes:

            new_solution.routes[tech_id].remove(node)
            unassigned_tasks.append(node)

            new_solution.changedRoute[tech_id] = True

        return new_solution, unassigned_tasks
        
    def route(solution, unassigned_tasks):
        new_solution = deepcopy(solution)
        all_nodes = [
        (tech_id, node)
        for tech_id, route in solution.routes.items()
        for node in route
        if node.node_type == NodeType.TASK
        ]

        k = int(max(1, len(solution.routes.items) * 0.1))
        removed_nodes = random.sample(all_nodes, k)
        

        return solution, unassigned_tasks
    
    def critical(solution, unassigned_tasks):
        
        return solution, unassigned_tasks
    
    def shaw(solution, unassigned_tasks):
        
        return solution, unassigned_tasks
    
    def skill(solution, unassigned_tasks):
        
        return solution, unassigned_tasks
    
    def type(solution, unassigned_tasks):
        
        return solution, unassigned_tasks  
        
    def __str__(self):
        pass

class Repair_Operator: 
    def __init__(self):
        pass
    def greedy(solution, unassigned_tasks, technicians, tasks):
        
        return solution, unassigned_tasks
    
    def regret(solution, unassigned_tasks, technicians, tasks):
        
        return solution, unassigned_tasks
    
    def random(solution, unassigned_tasks, technicians, tasks):
        
        return solution, unassigned_tasks
    

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
