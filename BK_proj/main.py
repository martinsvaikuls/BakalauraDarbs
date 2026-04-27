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

import urls

VANSIZE = 120
TASK_OVERTIME = datetime.timedelta(minutes=15)
TECH_OVERTIME = datetime.timedelta(minutes=60)
TECH_REST = datetime.timedelta(minutes=10) # rest_inbetween tasks

SHOP_DURATION = datetime.timedelta(minutes=10)
DEPOT_DURATION = datetime.timedelta(minutes=30)

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
        #!self.income = float(row["income"])
        self.priority = int(row["priority"])
        self.start_tw = (datetime.datetime.fromisoformat(str(row["start_tw"])))
        self.end_tw = (datetime.datetime.fromisoformat(str(row["end_tw"])))
        self.duration = int(row["duration"])
        self.created = (datetime.datetime.fromisoformat(str(row["created"])))

        self.lat = float(row["lat"])
        self.long = float(row["long"])
        self.location = self.lat, self.long
    def __str__(self):
        return f"{self.id} {self.skills} {self.duration} {self.priority} {self.start_tw} {self.end_tw} {self.location}"


class Technician:## ! resources is not set to master_id but to id, so resources do not go from one day to next day 
    def __init__(self, row):
        #self.id = int(row["id"]) #! not needed 
        self.master_id = int(row["master_id"])
        self.skills = set(ast.literal_eval(row["skills"]))

        #!self.resources = dict(ast.literal_eval(row["resources"]))

        self.start_tw = [datetime.datetime.fromisoformat(str(row["start_tw"]))]
        self.end_tw = [datetime.datetime.fromisoformat(str(row["end_tw"]))]

        self.lat = float(row["home_lat"])
        self.long = float(row["home_long"])
        self.home = self.lat, self.long

        #!self.created = int(row["created"])
        #!self.new_start_tw = 0

    def __str__(self):
        return f"{self.master_id} {self.skills} {self.start_tw} {self.end_tw} {self.home}"

class Depot:
    def __init__(self, row):
        self.id = int(row["id"])
        self.resources = dict(ast.literal_eval(row["resources"]))

        self.start_tw = [datetime.datetime.fromisoformat(str(row["start_tw"]))]
        self.end_tw = [datetime.datetime.fromisoformat(str(row["end_tw"]))]

        self.lat = float(row["home_lat"])
        self.long = float(row["home_long"])


class Shop:
    def __init__(self, row):
        self.id = int(row["id"])
        self.resources = dict(ast.literal_eval(row["resources"]))

        self.start_tw = [datetime.datetime.fromisoformat(str(row["start_tw"]))]
        self.end_tw = [datetime.datetime.fromisoformat(str(row["end_tw"]))]

        self.lat = float(row["home_lat"])
        self.long = float(row["home_long"])



class NodeType(StrEnum):
    TECH = "tech"
    TASK = "task"
    DEPOT = "depot"
    SHOP = "shop"


@dataclass(slots=True)
class Route_Node:
    node_type: NodeType
    id:  int
    start_time: datetime.datetime
    end_time: datetime.datetime

@dataclass(frozen=True, slots=True)
class Distance_Node:
    node_type: NodeType
    id:  int


class Distances: 
    def __init__(self):
        self.distances: Dict[Tuple[Distance_Node, Distance_Node], float] = {}
        self.coords: Dict[Distance_Node, Tuple[float, float]] = {}


    def add_coords(self, location_type, locations):
        for location in locations.values():
            if location_type is not NodeType.TECH:
                self.coords[Distance_Node(location_type, location.id)] = (location.lat, location.long)
            else:
                self.coords[Distance_Node(location_type, location.master_id)] = (location.lat, location.long)


    def euclidean_distance(self, a,b):
        return math.hypot(a[0] - b[0], a[1] - b[1])


    def get_distance(self, a: Distance_Node, b: Distance_Node):
        if (a, b) not in self.distances:
            self.update_distance(a,b)
             
        return self.distances[(a, b)]


    def update_distance(self, a,b): # ! 
        coord_a = self.coords[a]
        coord_b = self.coords[b]

        distance = self.euclidean_distance(coord_a,coord_b)

        self.distances[(a,b)] = distance
        self.distances[(b,a)] = distance


    def __str__(self):
        pass


class Weather: 
    def __init__(self):
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
    

    def __str__(self):
        pass


class Solution: 
    def __init__(self, technicians):
        self.tech_map = {t.master_id: t for t in technicians.values()}
        #!self.master_ids = {t.id: t.master_id for t in technicians} 

        self.routes = {t.master_id: [] for t in technicians.values()} 
        self.changedRoute = {t.master_id: False for t in technicians.values()} # checks if there is need to recalculate costs and incomes
        self.task_costs = dict[int,float]

        self.monetaryCost = {t.master_id: 0.0 for t in technicians.values()} #total cost per technician
        self.pathCost = {t.master_id: 0.0 for t in technicians.values()} #driving (cost for path)
        self.timeCost = {t.master_id: 0.0 for t in technicians.values()} #work (both for driving and work)
        self.weatherCost = {t.master_id: 0.0 for t in technicians.values()} #security (total cost for technician in all types of weather)
        self.resourcesCost = {t.master_id: 0.0 for t in technicians.values()} #costs of resources used
        self.income = {t.master_id: 0.0 for t in technicians.values()} #total income per tasks for technician

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
        #!new_solution.master_ids = self.master_ids

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
                current_tech_position = Distance_Node(NodeType.TECH, tech_id)
                cost_monetary = 0.0

                duration_work = 0.0
                cost_drive = 0.0

                weatherCost = 0.0

                incomeTech = 0.0

                resourceCost = 0.0

                route = routes[tech_id]
                ##for technician_id, route in routes.items():
                for node in route:
                    next_route_position =  Distance_Node(node.node_type, node.id)
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


    def __str__(self):
        masterID_list = []
        tech_id_list = []
        for master_id, route in self.routes.items():
            task_ids = [task.id for task in route]
            #master_id = self.master_ids[tech_id]
            masterID_list.append(f" \"{master_id}\": {task_ids},")
            #tech_id_list.append(f" \"{tech_id}\": {task_ids},")

        return  f"self.totalMonetaryCost" + "\n" + " ".join(masterID_list)
    """

    """     


class Operators: 
    def __init__(self):
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
    

    def destroy(self, solution, unassigned_tasks):
        match self.chosen_destroy:
            case 0:
                return self.destroy_ops.random(solution, unassigned_tasks)
            case 1:
                return self.destroy_ops.route(solution, unassigned_tasks)
            case 2:
                return self.destroy_ops.critical(solution, unassigned_tasks)
            case 3:
                return self.destroy_ops.shaw(solution, unassigned_tasks)
            case 4:
                return self.destroy_ops.skill(solution, unassigned_tasks)
            case 5:
                return self.destroy_ops.type(solution, unassigned_tasks)
            

    def repair(self, solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes):
        match self.chosen_repair:
            case 0:
                return self.repair_ops.greedy(solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes)
            case 1:
                return self.repair_ops.regret(solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes)
            case 2:
                return self.repair_ops.random(solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes)


    def renew_weights(self):
        self.weights_destroy[self.chosen_destroy] = (1.0 - self.reaction) * self.weights_destroy[self.chosen_destroy] + self.reaction * self.score
        self.weights_repair[self.chosen_repair] = (1.0 - self.reaction) * self.weights_repair[self.chosen_repair] + self.reaction * self.score
        
    def updateScore(self,new_score):
        self.score = new_score

    def __str__(self):
        pass


class Destroy_Operator: 
    def __init__(self):
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
    

    def skill(solution, unassigned_tasks, task): ### ! not finished
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
    def assign_feasability(self, task, tech, distances): # skills and time_windows
        can_assign = False
        

        for skill in task.skills:
            if not skill in tech.skills:
                return can_assign
        
        travel_time = distances.get_distance(Distance_Node(NodeType.TECH,tech.master_id),Distance_Node(NodeType.TASK,task.id))
        travel_time_home = distances.get_distance(Distance_Node(NodeType.TASK,task.id),Distance_Node(NodeType.TECH,tech.master_id))
        for i in range(len(tech.start_tw)):
            tech_arrives_before_end_of_task = tech.start_tw[i] + datetime.timedelta(minutes=travel_time) + datetime.timedelta(minutes=task.duration)
            if  tech_arrives_before_end_of_task > task.end_tw + TASK_OVERTIME:
                continue
            
            task_starts_before_end_of_work_shift = task.start_tw +  datetime.timedelta(minutes=task.duration)+ datetime.timedelta(minutes=travel_time_home) 
            if  task_starts_before_end_of_work_shift > tech.end_tw[i] + TECH_OVERTIME:
                continue

            can_assign = True
            break

        return can_assign

    def timeWindow_feasability(self, nodes, tech, distances, tasks):
        for i in range(len(tech.start_tw)):
            node_0 = Distance_Node(nodes[0].node_type, nodes[0].id)
            node_1 = Distance_Node(nodes[1].node_type, nodes[1].id)
            node_2 = Distance_Node(nodes[2].node_type, nodes[2].id)
            if nodes[0].node_type == NodeType.TASK:
                start_time_0 = tasks[nodes[0].id].start_tw
                duration_0 = datetime.timedelta(minutes=tasks[nodes[0].id].duration) + TECH_REST
            
            else:
                start_time_0 = tech.start_tw[i]
                duration_0 = datetime.timedelta(minutes=0)

            travelTime0_1 = distances.get_distance(node_0, node_1)

            end_tw_1 = tasks[nodes[1].id].end_tw
            duration_1 = tasks[nodes[1].id].duration

            
            travelTime0_1 = datetime.timedelta(minutes=travelTime0_1)
            duration_1 = datetime.timedelta(minutes=duration_1)

            if start_time_0 + duration_0 + travelTime0_1 + duration_1 <= end_tw_1 + TASK_OVERTIME:
                pass
            else:
                continue
            
            travelTime1_2 = distances.get_distance(node_1, node_2)

            travelTime1_2 = datetime.timedelta(minutes=travelTime1_2)

            if nodes[2].node_type == NodeType.TASK:
                end_tw_2 = tasks[nodes[2].id].end_tw
                duration_2 = datetime.timedelta(minutes=(tasks[nodes[2].id].duration)) + TECH_REST
                
                if end_tw_1 + duration_1 + travelTime1_2 + duration_2 <= end_tw_2 + TASK_OVERTIME:
                    return True
            
            else:
                end_tw_2 = tech.end_tw[i]
                duration_2 = datetime.timedelta(minutes=0)
                
                if end_tw_1 + duration_1 + travelTime1_2 + duration_2 <= end_tw_2 + TECH_OVERTIME:
                    return True

        return False
    
    def insertion_feasability(self, prev_nodes, insertion_node, next_nodes, tech, tasks, distances, insertionCehck=False):
        # * where it gets the end? #! what if it is TECH node, that does not have end time # * tech end has end_time whihc is start of tw
        last_prev_node = len(prev_nodes)-1
        #print()
        #print()
        #print()
        #print(prev_nodes)
        end_task = prev_nodes[last_prev_node].end_time 
        ### ! i do use the newly inserted route, hwoever it has no start or end...
        ### ! inserted goes further and tries to rebuild whihc is fine.
        ### ! do both shop and task insertion at same time
        ### ! update technician resources
        ### ! what if technician goes to depo/shop in his free time windwo and nothing else in that day prep for next day?

        # ! add weather
        travel_end_insertion = distances.get_distance(Distance_Node(prev_nodes[-1].node_type, prev_nodes[-1].id), Distance_Node(insertion_node.node_type, insertion_node.id))
        

        insertion_duration = datetime.timedelta(minutes=0)
        insertion_node_end = datetime.timedelta(minutes=0)
        travel_end_insertion = datetime.timedelta(minutes=travel_end_insertion)

        if insertion_node.node_type is NodeType.TASK:
            insertion_node_start = max(end_task + travel_end_insertion, tasks[insertion_node.id].start_tw) # *
            insertion_duration = datetime.timedelta(minutes=int(tasks[insertion_node.id].duration)) # *
            insertion_node_end = insertion_node_start + insertion_duration # * overtime?
            insertion_overtime = tasks[insertion_node.id].end_tw - insertion_node_end
            if insertion_overtime > TASK_OVERTIME:
                return [], False

        elif insertion_node.node_type is NodeType.SHOP:
            insertion_node_start = end_task + travel_end_insertion
            insertion_duration =  SHOP_DURATION
            insertion_node_end = insertion_node_start + insertion_duration
            
        elif insertion_node.node_type is NodeType.DEPOT:
            insertion_node_start = end_task + travel_end_insertion
            insertion_duration = DEPOT_DURATION
            insertion_node_end = insertion_node_start + insertion_duration
        else:
            print(insertion_node)
            print("error?")

        # * all technician homes from and to are inserted at construction
        # ! SHOP AND DEPOT does not have time_window
        #print(insertion_node_start)
        #print(insertion_node_end)
        if next_nodes[0].node_type is NodeType.TECH: # depends if it is last node or not or maybe just should somehow work with this in a different way
            for i in range(len(tech.start_tw)):
                if tech.start_tw[i] < insertion_node_start and tech.end_tw[i] < insertion_node_start:
                    next_task_start_feasability = tech.end_tw[i] + TECH_OVERTIME

        if next_nodes[0].node_type is NodeType.TASK:
            next_task_start_feasability = tasks[next_nodes[0].id].end_tw + TASK_OVERTIME
            next_task_duration = tasks[next_nodes[0].id].duration 
            next_task_duration = datetime.timedelta(minutes=next_task_duration)

        # ! add weather 
        travel_insertion_next = distances.get_distance(Distance_Node(insertion_node.node_type, insertion_node.id),Distance_Node(next_nodes[0].node_type, next_nodes[0].id))
        
        travel_insertion_next = datetime.timedelta(minutes=travel_insertion_next)

        if next_nodes[0].start_time is not None:
            start_next_node = next_nodes[0].start_time
        else: 
            start_next_node = max(tasks[next_nodes[0].id].start_tw, insertion_node_end + travel_insertion_next)

        
                                  
        if insertionCehck: #! in full rebuild after building the route up to new insertion could just stop if next step can be done
            if insertion_node_end + travel_insertion_next < start_next_node:
                insertion_node.start_time = insertion_node_start
                insertion_node.end_time = insertion_node_end
                return prev_nodes + [insertion_node] + next_nodes, True
               
        # ! building route not checking
        if next_nodes[0].node_type == NodeType.TASK:
            if insertion_node_end + travel_insertion_next + next_task_duration < next_task_start_feasability:
                insertion_node.start_time = insertion_node_start
                insertion_node.end_time = insertion_node_end

                return prev_nodes + [insertion_node] + next_nodes, True
        
        elif next_nodes[0].node_type == NodeType.TECH:
            if insertion_node_end + travel_insertion_next < next_task_start_feasability:
                insertion_node.start_time = insertion_node_start
                insertion_node.end_time = insertion_node_end

                return prev_nodes + [insertion_node] + next_nodes, True
        else:
            insertion_node.start_time = insertion_node_start
            insertion_node.end_time = insertion_node_end

            return prev_nodes + [insertion_node] + next_nodes, True

        return [], False


    def rightSide_twCheck(self, node, task):
        if task.end_tw + TASK_OVERTIME == node.end_time:
            return True
        return False


    def task_insertion(self, prev_nodes, insertion_task, next_nodes, tech, tasks, distances):
        new_route, feasable = self.insertion_feasability(prev_nodes, insertion_task, next_nodes, tech, tasks, distances, True)

        if not feasable: #! rebuilding whole route
            # ! should consider if both sides need rebuilding or can only left side or right side
            
            insertion_index = len(prev_nodes)
            # ! if ends at end_tw + overtime then on right side can't change anything 
            #print("insertion_index ", insertion_index)
            #print("prev_nodes[insertion_index-1] ", prev_nodes[insertion_index-1])
            
            is_technician = False
            if prev_nodes[insertion_index-1].node_type == NodeType.TECH:
                prev_node = tech
                is_technician = True
            else:
                #print(tasks[prev_nodes[insertion_index-1].id])
                prev_node = tasks[prev_nodes[insertion_index-1].id]

            not_right_side = False
            if not is_technician: 
                if self.rightSide_twCheck(prev_nodes[insertion_index-1], prev_node): #! unless it is technician
                    new_route, feasable = self.insertion_feasability(prev_nodes[-1], insertion_task, next_nodes[0], tech, tasks, distances)
                    route = [prev_nodes[-1]]+[insertion_task] + next_nodes
                    for i in range(len(route)-2):
                        new_route, feasable = self.insertion_feasability([route[i]], route[i+1], [route[i+2]], tech, tasks, distances)
                        route = new_route
                else:
                    not_right_side =True

            if not_right_side:
                route = prev_nodes + [insertion_task] + next_nodes
                #print(route)
                for i in range(len(route)-2): # * 0 1 2 3 4
                    if i+2 < len(route)-1:
                        break
                    if i+1 < len(route)-1:
                        break
                    if route[i+1].node_type == NodeType.TECH:
                        continue
                    new_route, feasable = self.insertion_feasability([route[i]], route[i+1], [route[i+2]], tech, tasks, distances)
                    route = new_route
                

        if not feasable:
            return [], False    
        
        return new_route, feasable


    def tech_goRestock(self, firstResourceFailurePoint, route, tech, tasks, distances, resources_needed, restocking_nodes):
        #!
        #insert shop if feasable and best place
        #resource timings
        #shops + depo
        #time_windows + distances

        # data type of all resources needed sorted from earliest to latest and ID, count
        # available space
        # what to do if no space available -> DEPO instead of SHOP
        # what if going to shop/depo twice is cheaper than once
        # SHOP/DEPO duration 10 minutes + travel duration to and from depo 30 min duration, because you can exhance space for free at shop you have to have free space
        # if restocked at shop +10% to cost
        # if can't restock return is_restocked = False
        candidates = []

        current_tech_location = Distance_Node(NodeType.TECH, tech.master_id)
        # 1. can we even restock
        cost = 0.0
        is_restocked = False
        restocking_route = route

        totalNeededResources = sum(resources_needed.values())
        techvanSize = sum(tech.resources.values())
        currentTech_availableVanSize = VANSIZE - techvanSize # wont work because tech vansize is a list
        
        for i in range(firstResourceFailurePoint):
            
            if route[i].node_type not in (NodeType.TASK, NodeType.TECH):
                continue
            
            if route[i].node_type is not NodeType.TASK:    
                techvanSize -= sum(tasks[route.id].resources.values()) 
                currentTech_availableVanSize = VANSIZE - techvanSize
            
            if currentTech_availableVanSize < totalNeededResources:
                continue
            ## if tech does not have necessary resources at this point we consider to go to depo/shop at any point in previous tasks.
            for shop in restocking_nodes:
                if shop.type is not NodeType.SHOP:
                    continue
                if not self.timeWindow_feasability([route[i], shop, route[i+1]], tech, distances, tasks):
                    continue

                new_route = route # ! should copy
                shop_node = Route_Node(NodeType.SHOP, shop.id, start_time=None, end_time=None)
                ## ! try to insert, maybe no need to rebuild, if can't insert then try to rebuild the route
                #pre_end + travel + insertion_duration + travel + next_start
                new_route, feasable = self.insertion_feasability(route[:i], shop_node, route[i:], tech, tasks, distances)

                ## ! try to rebuild from insertion outwards?
                new_route.insert(i + 1, shop_node)
                
                new_route, feasable = self.full_feasability(new_route)
                if not feasable:
                    continue

                candidates.append(new_route)


            for depot in restocking_nodes:
                if shop.type is not NodeType.DEPOT:
                    continue
                if not self.timeWindow_feasability([route[i], depot, route[i+1]], tech, distances, tasks):
                    continue

                new_route.insert(i + 1, Route_Node(NodeType.SHOP, shop.id, start_time=None, end_time=None))
                
                new_route, feasable = self.full_feasability(new_route)
                if not feasable:
                    continue
                candidates.append(new_route)

        
        # ! comparte candidates and choose best

        

        # for route
        return restocking_route, cost, is_restocked
        

    def routeCost_and_feasability(self, new_route, tech, distances, tasks, data, restocking_nodes): # creates new route considering everything that is hard feasability # weather is when insertion is possible 
        ### * resources
        ### time_windows + distance duration
        ### costs

        
        cost = 0.0
        current_techLocation = Distance_Node(NodeType.TECH, tech.master_id)
        
        currentTime = tech.start_tw 
        shiftEnd = tech.end_tw
        
        overTime = 0
        taskOverTime = 0

        ### need to collect all resources and check when each possible time to go to shop
        total_resourcesUsed = {}
        total_resourcesToRestock = {}

        needed_toRestock = False
        currentNode = 0
        firstResourceFailurePoint = -1

        ### ! recomputes too often
        for node in new_route:
            if node.node_type == NodeType.TASK:
                for resource_id, count in tasks[node.id].resources.items():
                    if resource_id not in total_resourcesUsed:
                        total_resourcesUsed[resource_id] = [0, 0.0] 

                    total_resourcesUsed[resource_id][0] += count # saves resouce count needed
                    total_resourcesUsed[resource_id][1] += data.resource_cost[resource_id] # saves cost
                

                    resource_data = total_resourcesUsed.get(resource_id)
                    resource_used = resource_data[0]
                    tech_resource_store = 0

                    if resource_id not in tech.resources.keys():
                        tech_resource_store = 0
                    else:
                        tech_resource_store = tech.resources.get(resource_id)
                    

                    if tech_resource_store < resource_used:
                        needed_toRestock = True
                        if firstResourceFailurePoint == -1:
                            firstResourceFailurePoint = currentNode

                        if resource_id not in total_resourcesToRestock:
                            total_resourcesToRestock[resource_id] = [0, None] 

                        if total_resourcesToRestock[resource_id][1] is None:
                            total_resourcesToRestock[resource_id][1] = currentNode # * node.id? saves first task when resource is needed
                        
                        total_resourcesToRestock[resource_id][0] = resource_used - tech_resource_store
                currentNode += 1  

        if needed_toRestock:
            restocking_route = [] ### ! cannot do this because shops influece currentNode variable or can do it? # can
            for node in new_route:
                if node.node_type in (NodeType.TASK, NodeType.TECH):
                    restocking_route.append
            
            # ! we insert both new restocking node and task at current insert location or not
            new_route, resource_costs, is_restocked = self.tech_goRestock(firstResourceFailurePoint, new_route, tech, tasks, distances, total_resourcesToRestock, restocking_nodes)
            if not is_restocked:
                return new_route, cost, False #not feasable to go to shop and retain all tasks
            
            ## * cost should be gotten from resources_needed ignoring the resources that needed restock ## * total_resources - resources_restocked
            for resource_id, values in total_resourcesToRestock.items():
                new_cost = total_resourcesUsed[resource_id][1] / total_resourcesUsed[resource_id][0] * (total_resourcesUsed[resource_id][0] - values[0]) 
                total_resourcesUsed[resource_id][0] -= values[0]
                total_resourcesUsed[resource_id][1] -= new_cost
            cost += resource_costs
            
            for cost_resource in total_resourcesUsed.values():
                cost += cost_resource[1]
        
            return new_route, cost, True
        
        else: ### ! if can insert task without affecting the surrounding tasks at current time then we just insert and move on
                ### ! time windows and what not
            """
            shop_node = Route_Node(NodeType.SHOP, shop.id, start_time=None, end_time=None)
            ## ! try to insert, maybe no need to rebuild, if can't insert then try to rebuild the route
            #pre_end + travel + insertion_duration + travel + next_start
            new_route, feasable = self.insertion_feasability(new_route[:i], shop_node, new_route[i:], tech, tasks, distances)

            ## ! try to rebuild from insertion outwards?
            new_route.insert(i + 1, shop_node)
            """
            # resources

    def calculateRouteCost(self, route, distances, tasks):
        
        return 1000.0

    def greedy(self, solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes):
        new_solution = solution.copy()
        indx = 0
        unfeasable_tasks = []
        removable_tasks = []
        while unassigned_tasks: ### set itteration count for stopping inf loop, ### no infinite loop because of pop
            candidates = []
            for task in unassigned_tasks:
                for tech_id, tech in technicians.items():
                    #print("AAAAAAAAAAAAAAAAAA: ", tech)
                    if not self.assign_feasability(tasks[task.id], tech, distances): ### Checks if skills and time_window is within limits
                        continue

                    
                    old_cost = new_solution.monetaryCost[tech.master_id]
                    new_task_insertion = Route_Node(NodeType.TASK, task.id, start_time=None, end_time=None)
                    for position in range(len(new_solution.routes[tech.master_id]) - 2): 
                        route = deepcopy(new_solution.routes[tech.master_id])
                        position += 1
                        ### * does not consider that task insertion can happen so that technciian starts task and all future tasks get ignored because current one takes too long
                        ### * does not consider if there is any available time (min duration of task)
                        ### * does not consider tech start home and end home
                        if route[position].node_type in [NodeType.SHOP, NodeType.DEPOT]:
                            continue
                        #print()
                        if route[position+1].node_type in [NodeType.SHOP, NodeType.DEPOT]:
                            continue
                        
                        if not self.timeWindow_feasability([route[position], new_task_insertion, route[position+1]], tech, distances, tasks):
                            continue

                        #print()
                        #print("positoni:", position)
                        #print(route[:position])
                        #print(route[position:])
                        new_route, feasable = self.task_insertion(route[:position], new_task_insertion, route[position:], tech, tasks, distances)

                        #new_route, new_cost, feasable = self.routeCost_and_feasability(new_route, tech, tasks, distances, data, restocking_nodes) 
                        
                        # ! restocking
                        if not feasable:
                            continue
                        

                        
                        new_cost = self.calculateRouteCost(new_route, distances, tasks) 

                        difference = new_cost - old_cost 
                        candidates.append((difference, new_route, tech.master_id, position, task.id))

                if not candidates:
                    unfeasable_tasks.append(task)
                    removable_tasks.append(task)

            indx += 1
            print(indx)
            for task in removable_tasks:
                unassigned_tasks = [t for t in unassigned_tasks if t.id != task.id]

            candidates.sort(key=lambda x: x[0])

            chosen = candidates[0]
            _, new_route, tech_id, pos, task_id = chosen

            new_solution.routes[tech_id] = new_route
            new_solution.changedRoute[tech_id] = True


            unassigned_tasks = [t for t in unassigned_tasks if t.id != task_id]

            
        return new_solution, unfeasable_tasks
    

    def regret(self, solution, unassigned_tasks, technicians, tasks, distances):
        new_solution = solution.copy()

        unfeasable_tasks = []


        return new_solution, unfeasable_tasks
    

    def random(self, solution, unassigned_tasks, technicians, tasks, distances):
        new_solution = solution.copy()

        unfeasable_tasks = []
        while unassigned_tasks:
            tech = random.choice(technicians)
            task_id = random.choice(unassigned_tasks)
            if self.assign_feasability(tasks[task_id], tech): ### Checks if skills and time_window is within limits
                route = new_solution.routes[tech.master_id]

                for position in range(len(route)):
                    new_route = route[:position] + Route_Node(NodeType.TASK, task_id, start_time=None, end_time=None) + route[position:]
                    new_cost = self.route_cost(new_route, tech)

                    #difference = new_cost - old_cost 
                    #candidates.append((difference, tech.master_id, position, tasks[task_id]))


        return new_solution, unfeasable_tasks
    
    def __str__(self):
        pass


class ALNS_ALgorithm: 
    def __init__(self, run_time = 60.0, simulatedAnnealing_temperature = 100.0, simulatedAnnealing_cooling = 0.995):
        self.run_time = run_time
        
        self.simulatedAnnealing_temperature = simulatedAnnealing_temperature
        self.simulatedAnnealing_cooling = simulatedAnnealing_cooling

        self.best_solution: Solution
        self.current_solution: Solution
        self.new_solution: Solution

        self.operators = Operators()
        self.score = 0

        self.tasks = {}
        self.technicians = {}
        self.unassigned_tasks = []

        self.distances = Distances()
        self.shops = {}
        self.depots = {}
        self.data = Resource_Data()
        


    def readData(self): # ***
        path = urls.taskFilePath
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                task_id = int(row["id"])
                self.tasks[task_id] = Task(row)  
        f.close()

        path = urls.technicianFilePath
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:

                master_id = int(row["master_id"])
                if master_id in self.technicians:
                    start_tw = datetime.datetime.fromisoformat(str(row["start_tw"]))
                    end_tw = datetime.datetime.fromisoformat(str(row["end_tw"]))
                    self.technicians[master_id].start_tw.append(start_tw)
                    self.technicians[master_id].end_tw.append(end_tw)
                    
                else:
                    self.technicians[master_id] = Technician(row)

        f.close()

        """
        path = urls.shopFilePath
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                shop_id = int(row["id"])
                self.shops[shop_id] = Shop(row)  
        f.close()

        path = urls.depotFilePath
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                depot_id = int(row["id"])
                self.depots[depot_id] = Depot(row)  
        f.close()
        """

        
    def construct(self): # ***

        self.distances.add_coords(NodeType.TASK, self.tasks)
        self.distances.add_coords(NodeType.TECH, self.technicians)
        #?self.distances = self.distances.add_coords(NodeType.DEPOT, self.tasks)
        #?self.distances = self.distances.add_coords(NodeType.SHOP, self.tasks)


        self.new_solution = Solution(self.technicians)


        for master_id, route in self.new_solution.routes.items():
            for i in range(len(self.technicians[master_id].start_tw)):
                route.append(Route_Node(NodeType.TECH, master_id, start_time=self.technicians[master_id].start_tw[i], end_time=self.technicians[master_id].start_tw[i]))
                route.append(Route_Node(NodeType.TECH, master_id, start_time=self.technicians[master_id].end_tw[i], end_time=self.technicians[master_id].end_tw[i])) 
        
        task_ids = list(self.tasks.keys())
        random.shuffle(task_ids)
        
        # * fill routes with tech home and home for every time window
        
        for id in task_ids:
            self.unassigned_tasks.append(Route_Node(NodeType.TASK, id, start_time=None, end_time=None))
        print(self.new_solution)
        ###! Greedy, have to finish operators first
        self.new_solution, self.unassigned_tasks = self.operators.repair(self.new_solution, self.unassigned_tasks, self.technicians, self.tasks, self.distances, self.data, [self.shops, self.depots])
        self.best_solution = deepcopy(self.new_solution)
        self.current_solution = deepcopy(self.new_solution)


    def selectOperators(self): # ***
        self.operators.roulette()


    def generateNewSolution(self): # ***
        self.new_solution, self.unassigned_tasks = self.operators.destroy(self.current_solution, self.unassigned_tasks)
        self.new_solution, self.unassigned_tasks = self.operators.repair(self.new_solution, self.unassigned_tasks, self.technicians, self.tasks, self.distances, self.data, [self.shops, self.depots])
        

    def acceptSimulatedAnnealingFunction(self): # ***
        if self.new_solution.totalMonetaryCost < self.current_solution.totalMonetaryCost:
            return True

        delta = self.new_solution.totalMonetaryCost - self.current_solution.totalMonetaryCost
        prob = min(1.0, math.exp(-delta / self.simulatedAnnealing_temperature))
        
        return random.random() < prob


    def updateWeights(self): # ***
        self.operators.renew_weights(self.score)


    def initialize(self):
        self.readData() # *
        self.construct() # *
        return self.best_solution
    
        start_time = time()
        while time() - start_time <= self.run_time:
            pass

        for i in range(1):
            self.selectOperators()
            
            self.generateNewSolution()

            if self.current_solution.totalMonetaryCost < self.new_solution.totalMonetaryCost:
                self.score = 1
            else:
                self.score = 3
            
            if self.new_solution.totalMonetaryCost < self.best_solution.totalMonetaryCost:
                self.best_solution = self.new_solution
                self.score = 5

            if self.acceptSimulatedAnnealingFunction():
                self.current_solution = self.new_solution

            self.updateWeights()
            self.simulatedAnnealing_temperature *= self.simulatedAnnealing_cooling

        return self.best_solution


    def __str__(self):
        pass


if __name__ == "__main__":
    algorithm = ALNS_ALgorithm()
    solution = algorithm.initialize()
    print(solution)

    
