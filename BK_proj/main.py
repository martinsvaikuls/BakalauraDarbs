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

VANSIZE = 120
TASK_OVERTIME = datetime.timedelta(minutes=15)
TECH_OVERTIME = datetime.timedelta(minutes=60)
TECH_REST = datetime.timedelta(minutes=10) # rest_inbetween tasks

class Resource_Data:
    def __init__(self):
        self.resource_cost = {
            1: 139,  2: 139,  3: 139,  4: 139,  5: 139,  6: 139,  7: 139,
            8: 119,  9: 119, 10: 119, 11: 119, 12: 119, 13: 119, 14: 119,
            15: 99, 16: 99, 17: 99, 18: 99, 19: 99, 20: 99, 21: 99,
            22: 79, 23: 79, 24: 79, 25: 79, 26: 79, 27: 79, 28: 79,
            29: 59, 30: 59, 31: 59, 32: 59, 33: 59, 34: 59, 35: 59,
            36: 39, 37: 39, 38: 39, 39: 39, 40: 39, 41: 39, 42: 39,
            43: 19, 44: 19, 45: 19, 46: 19, 47: 19, 48: 19, 49: 19,
        }
        self.technician_workHourCost = 20

        self.drivingHundredKMCost = 2.00*6
        self.drivingSpeedHr = 60
        self.drivingHourCost = self.drivingHundredKMCost*60/100


class Task: 
    def __init__(self, row):
        self.id = int(row["id"])
        self.skills = set(ast.literal_eval(row["skills"]))
        
        self.resources = [ast.literal_eval(row["resources"])]

        self.priority = int(row["priority"])
        self.start_tw = (datetime.datetime.fromisoformat(str(row["start_tw"])))
        self.end_tw = (datetime.datetime.fromisoformat(str(row["end_tw"])))
        self.duration = int(row["duration"])
        self.created = int(row["created"])

        self.lat = float(row["home_lat"])
        self.long = float(row["home_long"])

    def __str__(self, row):
        pass


class Technician: 
    def __init__(self, row):
        self.id = int(row["id"])
        self.master_id = int(row["master_id"])
        self.skills = set(ast.literal_eval(row["skills"]))

        self.resources = dict(ast.literal_eval(row["resources"]))

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
        self.task_costs = dict[int,float]

        self.monetaryCost = {t.id: 0.0 for t in technicians} #total cost per technician
        self.pathCost = {t.id: 0.0 for t in technicians} #driving (cost for path)
        self.timeCost = {t.id: 0.0 for t in technicians} #work (both for driving and work)
        self.weatherCost = {t.id: 0.0 for t in technicians} #security (total cost for technician in all types of weather)
        self.resourcesCost = {t.id: 0.0 for t in technicians} #costs of resources used
        self.income = {t.id: 0.0 for t in technicians} #total income per tasks for technician

        self.totalMonetaryCost = 0.0
        self.totalPathCost = 0.0
        self.totalTimeCost = 0.0
        self.totalWeatherCost = 0.0
        self.totalResourceCost = 0.0
        self.totalIncome = 0.0

        self.data = Resource_Data()


    def copy(self):
        new_solution = Solution.__new__(Solution)
        new_solution.tech_map = self.tech_map
        new_solution.master_ids = self.master_ids

        new_solution.routes = self.routes.copy()
        new_solution.changedRoute = self.changedRoute.copy()
        
        new_solution.monetaryCost = self.monetaryCost.copy()
        new_solution.pathCost = self.pathCost.copy()
        new_solution.timeCost = self.timeCost.copy()
        new_solution.weatherCost = self.weatherCost.copy()
        new_solution.resourcesCost = self.resourcesCost.copy()
        new_solution.income = self.income.copy()

        new_solution.totalMonetaryCost = self.totalMonetaryCost
        new_solution.totalPathCost = self.totalPathCost
        new_solution.totalTimeCost = self.totalTimeCost
        new_solution.totalWeatherCost = self.totalWeatherCost
        new_solution.totalResourceCost = self.totalResourceCost
        new_solution.totalIncome = self.totalIncome

        new_solution.data = self.data
        return new_solution
    
    def add_taskToRoute(self, tech_id, task_id, position):

        pass

    def updateCosts_Income(self, distances, tasks):
        routes = self.routes
        changedRoute = self.changedRoute

        totalPathCost = 0.0
        totalTimeCost = 0.0
        totalWeatherCost = 0.0
        totalIncome = 0.0
        totalResourceCost = 0.0

        for tech_id, cr in changedRoute.items():
            if cr:
                current_tech_position = Route_Node(NodeType.TECH, tech_id)
                cost_monetary = 0.0

                duration_work = 0.0
                cost_drive = 0.0

                weatherCost = 0.0

                incomeTech = 0.0

                resourceCost = 0.0

                route = routes[tech_id]
                ##for technician_id, route in routes.items():
                for node in route:
                    next_route_position = node
                    cost_driveToTask = distances.get_distance(current_tech_position, next_route_position) 
                    cost_drive += cost_driveToTask
                    
                    current_tech_position = next_route_position

                    ### weather
                    ######

                    if node.node_type == NodeType.TASK:
                        duration_workTask = tasks[node.id].duration
                        duration_work += duration_workTask
                        incomeTech += tasks[node.id].income
                        resourceCostTask = 0.0
                        for resource in tasks[node.id].resources:

                            resourceCostTask += self.data.resource_cost[resource] 
                        resourceCost += resourceCostTask
                        self.task_costs[node.id] = (cost_driveToTask+duration_workTask)*self.data.technician_workHourCost + resourceCostTask + cost_driveToTask*self.data.drivingHourCost



                self.pathCost[tech_id] = cost_drive * self.data.drivingHourCost                  

                cost_work = duration_work * self.data.workHourCost
                cost_drive = (self.pathCost[tech_id] / self.data.drivingHourCost) * self.data.workHourCost
                self.timeCost[tech_id] = cost_drive + cost_work

                ######### WEATHER

                self.weatherCost[tech_id] = weatherCost
                ################
                self.resourcesCost[tech_id] = resourceCost

                cost_monetary += self.pathCost[tech_id]
                cost_monetary += self.timeCost[tech_id]
                cost_monetary += self.weatherCost[tech_id]
                cost_monetary += self.resourcesCost[tech_id]
                
                self.monetaryCost[tech_id] = cost_monetary

                self.income[tech_id] = incomeTech
                
                self.changedRoute[tech_id] = False


            
            totalPathCost += self.pathCost[tech_id]
            totalTimeCost += self.timeCost[tech_id]
            totalWeatherCost += self.weatherCost[tech_id]
            totalIncome += self.income[tech_id]
            totalResourceCost += self.resourcesCost[tech_id]
        
        self.totalMonetaryCost = totalPathCost + totalTimeCost + totalWeatherCost
        self.totalPathCost = totalPathCost
        self.totalTimeCost = totalTimeCost
        self.totalWeatherCost = totalWeatherCost
        self.totalIncome = totalIncome
        self.totalResourceCost = totalResourceCost


    def copy_routes(self):
        return Solution(deepcopy(self.routes))


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
        new_solution = solution.copy()

        all_nodes = [
        (tech_id, node)
        for tech_id, route in new_solution.routes.items()
        for node in route
        if node.node_type == NodeType.TASK
        ]

        k = int(max(1, len(all_nodes) * 0.1))
        removed_nodes = random.sample(all_nodes, k)

        for tech_id, node in removed_nodes:
            if not new_solution.changedRoute[tech_id]:
                new_solution.routes[tech_id] = solution.routes[tech_id].copy()
            
            new_solution.routes[tech_id].remove(node)
            unassigned_tasks.append(node.id)

            new_solution.changedRoute[tech_id] = True

        return new_solution, unassigned_tasks


    def route(solution, unassigned_tasks):
        new_solution = solution.copy()

        all_routes = [
        (tech_id, route)
        for tech_id, route in solution.routes.items()
        ]

        k = int(max(1, len(all_routes) * 0.1))
        removed_nodes = random.sample(all_routes, k)

        for tech_id, route in removed_nodes:
            if not new_solution.changedRoute[tech_id]:
                new_solution.routes[tech_id] = solution.routes[tech_id].copy()

            new_solution.routes[tech_id] = []

            for node in route:
                if node.node_type == NodeType.TASK:
                    unassigned_tasks.append(node.id)

            new_solution.changedRoute[tech_id] = True


        return new_solution, unassigned_tasks
    

    def critical(solution, unassigned_tasks):
        new_solution = solution.copy()

        all_nodes = [
        (tech_id, node)
        for tech_id, route in new_solution.routes.items()
        for node in route
        if node.node_type == NodeType.TASK
        ]

        
        sorted_costs = sorted(new_solution.task_costs.items(), key=lambda x: x[1], reverse=True)

        k = int(max(1, len(sorted_costs) * 0.1))

        expensive_tasks = [task_id for task_id, cost in sorted_costs[:k]]


        for tech_id, node in all_nodes:
            if node.id in expensive_tasks:
                if not new_solution.changedRoute[tech_id]:
                    new_solution.routes[tech_id] = solution.routes[tech_id].copy()
                
                new_solution.routes[tech_id].remove(node)
                unassigned_tasks.append(node.id)

                new_solution.changedRoute[tech_id] = True


        return new_solution, unassigned_tasks
    

    def shaw(solution, unassigned_tasks): ### needs relatedness
        new_solution = solution.copy()



        return new_solution, unassigned_tasks
    

    def skill(solution, unassigned_tasks, task): ### not finished
        new_solution = solution.copy()

        all_nodes = [
        (tech_id, node)
        for tech_id, route in new_solution.routes.items()
        for node in route
        if node.node_type == NodeType.TASK
        ]

        skills = set()
        for tech_id, node in all_nodes:
            skills.update(task[node.id].skills)

        k = int(max(1, len(skills) * 0.1))
        chosen_skills = random.sample(skills, k)
        k_tasks = int(max(1, len(all_nodes) * 0.05))
        
        for skill in chosen_skills:
            removed_task_count = 0
            for tech_id, node in all_nodes:
                if removed_task_count == k_tasks:
                    break
                current_task = task.id[node.id]
                if skill in current_task.skills:
                    if not new_solution.changedRoute[tech_id]:
                        new_solution.routes[tech_id] = solution.routes[tech_id].copy()
                    
                    new_solution.routes[tech_id].remove(node)
                    unassigned_tasks.append(node.id)

                    new_solution.changedRoute[tech_id] = True
                    removed_task_count+=1   


        return new_solution, unassigned_tasks
    

    def type(solution, unassigned_tasks): ### needs types
        new_solution = solution.copy()

        return new_solution, unassigned_tasks  
        

    def __str__(self):
        pass


class Repair_Operator: 
    def __init__(self):
        pass
    def assign_feasability(task, tech, distances): # skills and time_windows
        can_assign = True

        for skill in task.skills:
            if not skill in tech.skills:
                return False
        travel_time = distances.getDistance(Route_Node(NodeType.TECH,tech.id),Route_Node(NodeType.TASK,task.id))
        if tech.start_tw + datetime.timedelta(minutes=travel_time) + datetime.timedelta(minutes=task.duration) > task.end_tw + TASK_OVERTIME:
            return False
        
        return can_assign

    def tech_goRestock(route, tech, tasks, distances, resources_needed, restocking_nodes):
        
        

        #insert shop if feasable and best place
        #resource timings
        #shops + depo
        #time_windows + distances

        # data type of all resources needed sorted from earliest to latest and ID, count
        # available space
        # what to do if no space available -> DEPO instead of SHOP
        # what if going to shop/depo twice is cheaper than once
        # SHOP/DEPO duration 10 minutes + travel duration to and from
        # if restocked at shop +10% to cost
        # if can't restock return is_restocked = False
        candidates = []

        current_tech_location = Route_Node(NodeType.TECH, tech.id)
        # 1. can we even restock
        cost = 0.0
        is_restocked = False
        restocking_route = route

        techvanSize = sum(tech.resources.values())
        currentTech_availableVanSize = VANSIZE - techvanSize # wont work because tech vansize is a list
        for node in route:
            if node.node_type == NodeType.TASK:
                for min_restockSize in restockNeeded:
                if currentTech_availableVanSize - min_restockSize >= 0:
                    for restocking_node in restocking_nodes:
                
                    spent_Resources = 

         ## if tech does not have necessary resources at this point we consider to go to depo/shop at any point in previous tasks.

        # for route
        return restocking_route, cost, is_restocked
        
    ##

    def routeCost_and_feasability(self, new_route, tech, distances, tasks, data, restocking_nodes): # creates new route considering everything that is hard feasability # weather is when insertion is possible 
        ### * resources
        ### time_windows + distance duration
        ### costs

        
        cost = 0.0
        current_techLocation = Route_Node(NodeType.TECH, tech.id)
        
        currentTime = tech.start_tw 
        shiftEnd = tech.end_tw
        
        overTime = 0
        taskOverTime = 0

        ### need to collect all resources and check when each possible time to go to shop
        total_resourcesUsed = {}
        total_resourcesToRestock = {}

        needed_toRestock = False
        currentTask = 0

        for nodeType, task in new_route.items():
            if nodeType == NodeType.TASK:
                for resource_id, count in tasks[task].resources.items():
                    if resource_id not in total_resourcesUsed:
                        total_resourcesUsed[resource_id] = [0, 0.0] 

                    total_resourcesUsed[resource_id][0] += count # saves resouce count needed
                    total_resourcesUsed[resource_id][1] += data.resource_cost[resource_id] # saves cost
                
                for resource_id, resource_count in tech.resources.items():
                    if total_resourcesUsed[resource_id]:
                        if resource_count < total_resourcesUsed.get(resource_id)[0]:
                            needed_toRestock = True

                            if resource_id not in total_resourcesToRestock:
                                    total_resourcesToRestock[resource_id] = [0, None] 

                            if total_resourcesToRestock[resource_id][1] is None:
                                total_resourcesToRestock[resource_id][1] = task # saves first task when resource is needed
                            total_resourcesToRestock[resource_id][0] = total_resourcesToRestock - resource_count
                                           
                currentTask += 1


        if needed_toRestock:
            new_route, resource_costs, is_restocked = self.tech_goRestock(new_route, tech, tasks, distances, total_resourcesToRestock, restocking_nodes)
            if not is_restocked:
                return cost, False #not feasable to go to shop and retain all tasks
            
            ## * cost should be gotten from resources_needed ignoring the resources that needed restock ## * total_resources - resources_restocked
            for resource_id, values in total_resourcesToRestock.items():
                new_cost = total_resourcesUsed[resource_id][1] / total_resourcesUsed[resource_id][0] * (total_resourcesUsed[resource_id][0] - values[0]) 
                total_resourcesUsed[resource_id][0] -= values[0]
                total_resourcesUsed[resource_id][1] -= new_cost
            cost += resource_costs
            
            for cost_resource in total_resourcesUsed.values():
                cost += cost_resource[1]
        else:
            for task in new_route:
                if not task.resources.issubset(tech.resources):
                    # go to nerest shop
                    # need to consider best time to go to shop 
                    pass
                
                next_location = Route_Node(NodeType.TASK, task.id)
                travel_duration = distances.get_distance(current_techLocation,next_location)

        # resources
        
        return cost
    

    def timeWindow_feasability(nodes, tech, distances, tasks):
        if nodes[0].node_type == NodeType.TASK:
            start_time_0 = tasks[nodes[0].id].start_tw
            duration_0 = tasks[nodes[0].id].duration + TECH_REST
        
        else:
            start_time_0 = tech[nodes[0].id].start_tw
            duration_0 = 0

        travelTime0_1 = distances.get_distance(nodes[0], nodes[1])

        end_tw_1 = tasks[nodes[1].id].end_tw
        duration_1 = tasks[nodes[1].id].duration

        if start_time_0 + duration_0 + travelTime0_1 + duration_1 <= end_tw_1 + TASK_OVERTIME:
            pass
        else:
            return False
        
        travelTime1_2 = distances.get_distance(nodes[1], nodes[2])

        if nodes[2].node_type == NodeType.TASK:
            end_tw_2 = tasks[nodes[2].id].start_tw
            duration_2 = tasks[nodes[2].id].duration + TECH_REST
            
            if end_tw_1 + duration_1 + travelTime1_2 + duration_2 <= end_tw_2 + TASK_OVERTIME:
                return True
        
        else:
            end_tw_2 = tech[nodes[2].id].start_tw
            duration_2 = 0
            
            if end_tw_1 + duration_1 + travelTime1_2 + duration_2 <= end_tw_2 + TECH_OVERTIME:
                return True

        return False


    def greedy(self, solution, unassigned_tasks, technicians, tasks, distances):
        new_solution = solution.copy()

        unfeasable_tasks = []
        
        while unassigned_tasks: ### set itteration count for stopping inf loop, ### no infinite loop because of pop
            candidates = []
            for task_id in unassigned_tasks:
                for tech in technicians:
                    if not self.assign_feasability(tasks[task_id], tech, distances): ### Checks if skills and time_window is within limits
                        continue

                    route = new_solution.routes[tech.id]
                    old_cost = new_solution.monetaryCost[tech.id]
                    new_task_insertion = Route_Node(NodeType.TASK, task_id)
                    for position in range(len(route)): 
                        ### ! does not consider that task insertion can happen so that technciian starts task and all future tasks get ignored because current one takes too long
                        ### ! does not consider if there is any available time (min duration of task)
                        ### ! does not consider tech start home and end home
                        if route[position].node_type in [NodeType.SHOP, NodeType.DEPOT]:
                            continue
                        if route[position+1].node_type in [NodeType.SHOP, NodeType.DEPOT]:
                            continue

                        if not self.timeWindow_feasability([route[position], new_task_insertion, route[position+1]], distances, tasks):
                            continue

                        new_route = route[:position] +  new_task_insertion + route[position:]
                        new_cost, feasable = self.routeCost_and_feasability(new_route, tech, distances, tasks) 
                    
                        if not feasable:
                            break

                        difference = new_cost - old_cost 
                        candidates.append((difference, tech.id, position, tasks[task_id]))

            if not candidates:
                unfeasable_tasks.append(unassigned_tasks.pop(0))
                continue

            candidates.sort(key=lambda x: x[0])

            chosen = candidates[0]
            _, tech_id, pos, task = chosen

            new_solution.add_task(tech_id, task, pos)
            unassigned_tasks.remove(task)

            
        return new_solution, unfeasable_tasks
    

    def regret(self, solution, unassigned_tasks, technicians, tasks):
        new_solution = solution.copy()

        unfeasable_tasks = []


        return new_solution, unfeasable_tasks
    

    def random(self, solution, unassigned_tasks, technicians, tasks):
        new_solution = solution.copy()

        unfeasable_tasks = []
        while unassigned_tasks:
            tech = random.choice(technicians)
            task_id = random.choice(unassigned_tasks)
            if self.assign_feasability(tasks[task_id], tech): ### Checks if skills and time_window is within limits
                route = new_solution.routes[tech.id]

                for position in range(len(route)):
                    new_route = route[:position] + Route_Node(NodeType.TASK,task_id) + route[position:]
                    new_cost = self.route_cost(new_route, tech)

                    #difference = new_cost - old_cost 
                    #candidates.append((difference, tech.id, position, tasks[task_id]))


        return new_solution, unfeasable_tasks
    

    

    def __str__(self, row):
        pass


class ALNS_ALgorithm: 
    def __init__(self, row):
        self.simulatedAnnealing_temperature = 100.0
        self.best_solution = Solution()
        self.operators = Operators()

        self.tasks = dict(int,Task())
        self.technicians = dict(int,Technician())


    def selectOperators():
        pass


    def generateNewSolution():
        pass


    def acceptSimulatedAnnealingFunction():
        pass


    def updateWeights(self,score):
        self.operators.renew_weights(score)


    def initialize():
        pass


    def __str__(self, row):
        pass

