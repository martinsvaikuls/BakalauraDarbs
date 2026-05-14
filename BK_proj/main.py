import random
import math
import csv
import ast
import numpy as np
import json
import datetime
import time
import os

from copy import deepcopy

from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import StrEnum

import urls

#import weather
import xarray as xr

VANSIZE = 120
TASK_OVERTIME = datetime.timedelta(minutes=30)
TECH_OVERTIME = datetime.timedelta(minutes=60)
TECH_LAST_TASK = datetime.timedelta(hours=16)

TECH_REST = datetime.timedelta(minutes=10) # rest_inbetween tasks

SHOP_DURATION = datetime.timedelta(minutes=5)
SHOP_COST_MULT = 1.2
DEPOT_DURATION = datetime.timedelta(minutes=15)

DEPOT_TEST = True
SHOP_TEST = False
WEATHER_TEST = True

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
        self.technician_workHourCost = 10
        self.workHourCost = 10
        self.drivingHundredKMCost = 2.00*6
        self.drivingSpeedHr = 50
        self.drivingHourCost = self.drivingHundredKMCost * self.drivingSpeedHr / 100


class Task: 
    def __init__(self, row):
        self.id = int(row["id"])
        self.skills = set(ast.literal_eval(row["skills"]))
        
        self.resources = ast.literal_eval(row["resources"])
        self.income = float(row["income"])
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

        self.resources = dict(ast.literal_eval(row["resources"]))

        self.start_tw = [datetime.datetime.fromisoformat(str(row["start_tw"]))]
        self.end_tw = [datetime.datetime.fromisoformat(str(row["end_tw"]))]

        self.lat = float(row["home_lat"])
        self.long = float(row["home_long"])
        self.home = self.lat, self.long


    def __str__(self):
        return f"{self.master_id} {self.skills} {self.start_tw} {self.end_tw} {self.home}"

class Depot:
    def __init__(self, row):
        self.id = int(row["id"])
        self.resources = dict(ast.literal_eval(row["resources"]))

        self.start_tw = datetime.datetime.fromisoformat(str(row["start_tw"]))
        self.end_tw = datetime.datetime.fromisoformat(str(row["end_tw"]))

        self.lat = float(row["lat"])
        self.long = float(row["long"])
        self.location = self.lat, self.long

    def __str__(self):
        return f"{self.id}  {self.start_tw} {self.end_tw} {self.location}"

class Shop:
    def __init__(self, row):
        self.id = int(row["id"])
        self.resources = dict(ast.literal_eval(row["resources"]))

        self.start_tw = datetime.datetime.fromisoformat(str(row["start_tw"]))
        self.end_tw = datetime.datetime.fromisoformat(str(row["end_tw"]))

        self.lat = float(row["lat"])
        self.long = float(row["long"])
        self.location = self.lat, self.long
    def __str__(self):
        return f"{self.id}  {self.start_tw} {self.end_tw} {self.location}"


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

    def copy_node(self):
        return Route_Node(
            node_type=self.node_type,
            id=self.id,
            start_time=self.start_time,
            end_time=self.end_time
        )

    def __str__(self):
        if self.node_type == NodeType.TECH:
            return f"[TECH] id={self.id} | {self.start_time}"
        
        return f"[TASK] id={self.id} | {self.start_time} → {self.end_time}"

@dataclass(frozen=True, slots=True)
class Distance_Node:
    node_type: NodeType
    id:  int


class Weather: 
    def __init__(self):
        # crashes per 100 million km 
        #self.average = 160.932
        #self.sunshine = 197.624
        #self.rain = 226.109
        #self.snow = 446.264

        self.wind_multiplier = 1.017 #163.668/160.932
        # cost per km
        # cost per crash 26081 (T. R. Miller & A. S. McKnight, 2021)
        self.average = 0.04197
        self.sunshine = 0.05154
        self.rain = 0.05897
        self.snow = 0.11639

        self.sunshine_slow = 1
        self.rain_slow = 1.06
        self.snow_slow = 1.11
        self.wind_slow = 1

        self.ds = xr.open_dataset(
            urls.weather,
            engine="cfgrib",
            backend_kwargs={"errors": "ignore"}
        )
        
        self.t2m = self.ds["t2m"] 
        self.u10 = self.ds["u10"]
        self.v10 = self.ds["v10"]
        self.tcc = self.ds["tcc"]
        self.tp = xr.open_dataset(urls.weather, engine="cfgrib", filter_by_keys={'shortName':'tp'})

    def get_data(self, data_type, coord, time):
        lat, long = coord
        return data_type.sel(
            time=time,
            latitude=lat,
            longitude=long,
            method="nearest"
            )

    def get_temp(self, coord, time):
        temp = self.get_data(self.t2m, coord, time)

        return float(temp)
    
    def get_cloud(self, coord, time):
        clouds = self.get_data(self.tcc, coord, time)

        return float(clouds)
    
    def get_wind(self, coord, time):
        wind_u = self.get_data(self.u10, coord, time)
        wind_v = self.get_data(self.v10, coord, time)

        return float(wind_u), float(wind_v) 
    
    def cross_wind(self, wind_u, wind_v, coord_start, coord_end, route_length):
        lat1, lon1 = coord_start
        lat2, lon2 = coord_end
        dx = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
        dy = (lat2 - lat1) * 110.574

        if route_length == 0:
            return 0.0
        
        cross_winds = abs(wind_u * dy - wind_v * dx) / (route_length*1000)

        return cross_winds

    def get_percipitation(self, coord, time):
        lat, lon = coord
 
        
        tp_location = self.tp.sel(latitude=lat, longitude=lon, method="nearest")
        
 
        base_time = tp_location["time"].sel(time=time, method="nearest")
        tp_time = tp_location.sel(time=base_time)
        

        dt_seconds = np.abs(tp_time["valid_time"].values - np.datetime64(time))
        nearest_step = int(dt_seconds.argmin())

        percipitation = float(tp_time["tp"].isel(step=nearest_step).values) * 1000

        
        if np.isnan(percipitation):
            return 0.0
        return percipitation
   

    def getWeather(self, start: Distance_Node, end: Distance_Node, travel_start_time, travel_end_time, distances):
        cost_per_km = self.average
        slow_downFactor = 1.0
        coord_start = distances.coords[start]
        coord_end = distances.coords[end] # uses nearest

        hm, route_length = distances.get_distance(start,end)


        temp_start = self.get_temp(coord_start, travel_start_time)
        temp_end = self.get_temp(coord_end, travel_end_time)

        cloud_start = self.get_cloud(coord_start, travel_start_time)
        cloud_end = self.get_cloud(coord_end, travel_end_time)

        wind_start = self.get_wind(coord_start, travel_start_time)
        wind_end = self.get_wind(coord_end, travel_end_time)

        crosswinds_start = self.cross_wind(wind_start[0], wind_start[1], coord_start, coord_end, route_length)
        crosswinds_end = self.cross_wind(wind_end[0], wind_end[1], coord_start, coord_end, route_length)

        percipitation_start = self.get_percipitation(coord_start, travel_start_time)
        percipitation_end = self.get_percipitation(coord_end, travel_end_time)    

        temp_average = (temp_end + temp_start)/2 - 273.15 
        cloud_average = (cloud_start + cloud_end)/2 
        cross_wind_average = (crosswinds_start + crosswinds_end)/2
        percipitation_average = (percipitation_start + percipitation_end)/2
        
        #print(temp_average, percipitation_average, cross_wind_average)

        if temp_average < 0.0 and percipitation_average >= 0.1:
            slow_downFactor = self.snow_slow
            cost_per_km = self.snow
        elif temp_average >= 0.0 and percipitation_average >= 0.1:
            slow_downFactor = self.rain_slow
            cost_per_km = self.rain

        if cross_wind_average >= 25.0:
            cost_per_km *= self.wind_multiplier
            #slow_downFactor = slow_downFactor
            
        return cost_per_km, slow_downFactor


    def __str__(self):
        pass

class Distances: 
    def __init__(self):
        #self.distances: Dict[Tuple[Distance_Node, Distance_Node], float] = {}
        self.distances: Dict[Tuple[Distance_Node, Distance_Node], tuple[float,float]] = {}
        self.weather: Dict[Tuple[Distance_Node, Distance_Node, datetime.datetime], tuple[float,float]] = {}
        
        #self.distances: Dict[Tuple[Distance_Node, Distance_Node], tuple[float,float,float,float]] = {} # distance, duration, weather_costFactor, weather_slowDown
        self.coords: Dict[Distance_Node, Tuple[float, float]] = {}


    def add_coords(self, location_type, locations):
        for location in locations.values():
            if location_type is not NodeType.TECH:
                self.coords[Distance_Node(location_type, location.id)] = (location.lat, location.long)
            else:
                self.coords[Distance_Node(location_type, location.master_id)] = (location.lat, location.long)

    def add_distances_from_file(self):
        distance_file = urls.distances
        file_exists = os.path.exists(distance_file)
        existing_keys = set()

        if file_exists:
            with open(distance_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile, delimiter=';')
                for row in reader:
                    a = Distance_Node(row["a_nodetype"], int(row["a_id"]))
                    b = Distance_Node(row["b_nodetype"], int(row["b_id"]))

                    self.distances[(a,b)] = (float(row["distance"]),float(row["duration"]))
                    
                   
            infile.close()

        weather_file = urls.weather_cahce
        file_exists = os.path.exists(weather_file)
        existing_keys = set()
        
        if file_exists:
            with open(weather_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile, delimiter=';')
                for row in reader:
                    a = Distance_Node(row["a_nodetype"], int(row["a_id"]))
                    b = Distance_Node(row["b_nodetype"], int(row["b_id"]))
                    c = datetime.datetime.fromisoformat(str(row["time"]))

                    self.weather[(a,b,c)] = (float(row["cost_factor"]),float(row["slow_downFactor"]))
                    
                   
            infile.close()
        return

    def euclidean_distance(self, a,b):
        lat1, lon1 = a
        lat2, lon2 = b

        dx = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
        dy = (lat2 - lat1) * 110.574


  
        return math.hypot(dx, dy), math.hypot(dx, dy)/50*60
        #return (math.hypot(a[0] - b[0], a[1] - b[1]))*60

    def get_distance_api(self, a: Distance_Node, b: Distance_Node):
        
        return self.distances[(a, b)][1]

    def get_distance(self, a: Distance_Node, b: Distance_Node): #
        if (a, b) not in self.distances:
            self.update_distance(a,b)

        
             
        return self.distances[(a, b)][0], self.distances[(a, b)][1]

    def get_weather(self, a: Distance_Node, b: Distance_Node, start, end, weather: Weather):
        nearest_hour_start = None
        
        if start.minute >= 30:
        # Round up
            nearest_hour_start = start.replace(minute=0) + datetime.timedelta(hours=1)
        else:
            # Round down
            nearest_hour_start = start.replace(minute=0)

        nearest_hour_start = (nearest_hour_start.replace(second=0, microsecond=0)).isoformat()
        if (a,b,nearest_hour_start) not in self.weather:
            self.update_weather(a,b,nearest_hour_start,end,weather)

        return self.weather[(a,b,nearest_hour_start)][0], self.weather[(a,b,nearest_hour_start)][1]

    def update_distance(self, a,b): # ! 
        coord_a = self.coords[a]
        coord_b = self.coords[b]

        distance, duration = self.euclidean_distance(coord_a,coord_b)

    
        self.distances[(a,b)] = (distance,duration)
        self.distances[(b,a)] = (distance,duration)

    def update_weather(self,a,b,start,end,weather):
        cost_factor, slow_downFactor = weather.getWeather(a,b,start,end,self)
        
        self.weather[(a,b,start)] = (cost_factor,slow_downFactor)
        self.weather[(b,a,start)] = (cost_factor,slow_downFactor)


    def cache(self):
        distance_file = urls.distances
        file_exists = os.path.exists(distance_file)
        existing_keys = set()

        if file_exists:
            with open(distance_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile, delimiter=';')
                for row in reader:
                    key = (
                        row["a_nodetype"], int(row["a_id"]),
                        row["b_nodetype"], int(row["b_id"])
                    )
                    existing_keys.add(key)
                   
            infile.close()

        with open(distance_file, 'a', newline='', encoding='utf-8') as outfile: 
            fieldnames = ["a_nodetype","a_id","b_nodetype","b_id","distance","duration"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
            
            if not file_exists:
                writer.writeheader()

            for keys, values in self.distances.items():
                key = (keys[0].node_type,keys[0].id,keys[1].node_type,keys[1].id)
                
                if key in existing_keys:
                    continue

                row = {"a_nodetype":keys[0].node_type,"a_id":keys[0].id,"b_nodetype":keys[1].node_type,"b_id":keys[1].id,"distance":values[0],"duration":values[1]}

                writer.writerow(row)
            
        outfile.close()


        weather_file = urls.weather_cahce
        file_exists = os.path.exists(weather_file)
        existing_keys = set()

        if file_exists:
            with open(weather_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile, delimiter=';')
                for row in reader:
                    key = (
                        row["a_nodetype"], int(row["a_id"]),
                        row["b_nodetype"], int(row["b_id"]),
                        datetime.datetime.fromisoformat(str(row["time"]))
                    )
                    existing_keys.add(key)
                   
            infile.close()

        with open(weather_file, 'a', newline='', encoding='utf-8') as outfile: 
            fieldnames = ["a_nodetype","a_id","b_nodetype","b_id","time","cost_factor","slow_downFactor"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
            
            if not file_exists:
                writer.writeheader()

            for keys, values in self.weather.items():
                key = (keys[0].node_type,keys[0].id,keys[1].node_type,keys[1].id,keys[2])
                
                if key in existing_keys:
                    continue

                row = {"a_nodetype":keys[0].node_type,"a_id":keys[0].id,"b_nodetype":keys[1].node_type,"b_id":keys[1].id,
                       "time":keys[2],
                       "cost_factor":values[0],"slow_downFactor":values[1]}

                writer.writerow(row)
            
        outfile.close()


        return


    def __str__(self):
        pass



class Solution: 
    def __init__(self, technicians, tasks):
        self.tech_map = {t.master_id: t for t in technicians.values()}
        self.tasks = tasks
        #self.tasks_decline = {t.master_id: [] for t in technicians.values()}
        self.routes = {t.master_id: [] for t in technicians.values()}
        self.resources = {t.master_id: [] for t in technicians.values()} 
        self.changedRoute = {t.master_id: False for t in technicians.values()} # checks if there is need to recalculate costs and incomes
        ### ! task costs
        self.task_costs = {t.id: 0.0 for t in tasks.values()}
        self.monetaryCost = {t.master_id: 0.0 for t in technicians.values()} #total cost per technician
        ### ! DRIVING 
        self.pathCost = {t.master_id: 0.0 for t in technicians.values()} #driving (cost for path)
        self.timeCost = {t.master_id: 0.0 for t in technicians.values()} #work (both for driving and work)
        ### ! WEATHER
        self.weatherExtraTime = {t.master_id: 0.0 for t in technicians.values()}
        self.weatherSafetyRiskKm = {t.master_id: 0.0 for t in technicians.values()}
        self.weatherCost = {t.master_id: 0.0 for t in technicians.values()} #security (total cost for technician in all types of weather)
        ### ! RESOURCES 
        self.shopCost = {t.master_id: 0.0 for t in technicians.values()}
        self.depotCost = {t.master_id: 0.0 for t in technicians.values()}
        self.resourcesCost = {t.master_id: 0.0 for t in technicians.values()} #costs of resources used
        
        self.income = {t.master_id: 0.0 for t in technicians.values()} #total income per tasks for technician

        self.totalMonetaryCost = 0.0

        self.totalPathCost = 0.0
        self.totalPathKm = 0.0
        self.totalTimeCost = 0.0
        self.totalOverTime = 0.0

        self.totalWeatherExtraTime = 0.0
        self.totalWeatherSafetyRiskKm = 0.0
        self.totalWeatherCost = 0.0

        self.totalShopCost = 0.0
        self.totalDepotCost = 0.0
        self.totalResourceCost = 0.0
        
        self.totalIncome = 0.0

        self.forgottenTaskCost = 0.0
        self.weight = 0.0

        self.data = Resource_Data()


    def copy(self):
        new_solution = Solution.__new__(Solution)
        new_solution.tech_map = self.tech_map

        new_solution.tasks = self.tasks.copy()
        new_solution.routes = self.routes.copy()
        new_solution.changedRoute = self.changedRoute.copy()
        new_solution.task_costs = self.task_costs.copy()
        
        new_solution.monetaryCost = self.monetaryCost.copy()

        new_solution.totalMonetaryCost = self.totalMonetaryCost

        #### ! DRIVING
        new_solution.pathCost = self.pathCost.copy()
        new_solution.timeCost = self.timeCost.copy()

        new_solution.totalPathCost = self.totalPathCost
        new_solution.totalTimeCost = self.totalTimeCost

        ### ! WEATHER
        new_solution.weatherExtraTime = self.weatherExtraTime.copy()
        new_solution.weatherSafetyRiskKm = self.weatherSafetyRiskKm.copy()
        new_solution.weatherCost = self.weatherCost.copy()

        new_solution.totalWeatherExtraTime = self.totalWeatherExtraTime
        new_solution.totalWeatherSafetyRiskKm = self.totalWeatherSafetyRiskKm
        new_solution.totalWeatherCost = self.totalWeatherCost

        ### ! RESOURCES
        new_solution.shopCost = self.shopCost.copy()
        new_solution.depotCost = self.depotCost.copy()
        new_solution.resourcesCost = self.resourcesCost.copy()

        new_solution.totalShopCost = self.totalShopCost
        new_solution.totalDepotCost = self.totalDepotCost
        new_solution.totalResourceCost = self.totalResourceCost

        ### ! INCOME / PENALTY
        new_solution.income = self.income.copy()
        
        new_solution.totalIncome = self.totalIncome
        new_solution.forgottenTaskCost = self.forgottenTaskCost
        

        new_solution.weight = self.weight
        new_solution.data = self.data
        return new_solution
    

        pass
        #! the list mutates

    def unUsedTasks(self, tasks, unusedTasks):
        TEST = 100
        totalCost = 0.0
        for node in unusedTasks:
            totalCost += tasks[node.id].income #* tasks[node.id].priority #* TEST

        self.forgottenTaskCost = totalCost

    def updateCosts_Income(self, distances, tasks, unusedTasks, weather):
        self.unUsedTasks(tasks, unusedTasks)
        
        routes = self.routes
        changedRoute = self.changedRoute

        totalPathCost = 0.0
        totalTimeCost = 0.0
        totalWeatherCost = 0.0
        totalIncome = 0.0

        totalWeatherExtraTime = 0.0
        totalWeatherSafetyRiskKm = 0.0
        totalShopCost = 0.0
        totalDepotCost = 0.0
        totalResourceCost = 0.0

        for tech_id, cr in changedRoute.items():
            cr = True
            if cr:
                
                current_tech_postiion_time = None
                cost_monetary = 0.0

                duration_work = 0.0
                cost_drive = 0.0

                weatherExtraTime = 0.0
                weatherSafetyRiskKm = 0.0
                weatherCost = 0.0

                incomeTech = 0.0

                resourceCost = 0.0
                travel_minutes = 0.0
                route = routes[tech_id]


                ### ! resources
                total_resourcesUsed = {}
                total_resourcesToRestock = {}
                needed_toRestock = False
                currentNode = 0
                firstResourceFailurePoint = -1
                for node in route:
                    if node.node_type == NodeType.TASK:
                        for resource_id in tasks[node.id].resources:
                            if resource_id not in total_resourcesUsed:
                                total_resourcesUsed[resource_id] = [0, 0.0] 

                            total_resourcesUsed[resource_id][0] += 1 # saves resouce count needed
                            total_resourcesUsed[resource_id][1] += self.data.resource_cost[resource_id] # saves cost
                        
                            resource_data = total_resourcesUsed.get(resource_id)
                            resource_used = resource_data[0]
                            tech_resource_store = 0

                            if resource_id not in self.tech_map[tech_id].resources.keys():
                                tech_resource_store = 0
                            else:
                                tech_resource_store = self.tech_map[tech_id].resources.get(resource_id)
                            
                            if tech_resource_store < resource_used:
                                needed_toRestock = True
                                if firstResourceFailurePoint == -1:
                                    firstResourceFailurePoint = currentNode

                                if resource_id not in total_resourcesToRestock:
                                    total_resourcesToRestock[resource_id] = [0, None] 

                                if total_resourcesToRestock[resource_id][1] is None:
                                    total_resourcesToRestock[resource_id][1] = currentNode # * node.id? saves first task when resource is needed
                                
                                total_resourcesToRestock[resource_id][0] = resource_used - tech_resource_store
                
                shop = False
                depot = False

                for i in range(len(route)-2):
                    if route[i].node_type == NodeType.TECH and route[i+1].node_type == NodeType.TECH:
                        continue
                    
                    current_tech_position = Distance_Node(route[i].node_type, route[i].id)
                    next_route_position =  Distance_Node(route[i+1].node_type, route[i+1].id)
                    
                    ### ! DRIVING
                    travel_km, travel_minutes = distances.get_distance(current_tech_position, next_route_position) # * minutes
                    cost_drive += travel_minutes

                    ### ! WEATHER calc
                    travel_start = route[i].end_time
                    travel_end = travel_start + datetime.timedelta(minutes=travel_minutes)
                    cost_factor, slow_downFactor = distances.get_weather(current_tech_position,next_route_position,travel_start,travel_end,weather)
                    
                    ### ! WEATHER assign
                    weatherExtraTime += travel_minutes * slow_downFactor - travel_minutes
                    weatherSafetyRiskKm += travel_km * cost_factor
                    weatherCost = weatherExtraTime * (self.data.technician_workHourCost + self.data.drivingHourCost) + weatherSafetyRiskKm

                    if route[i].node_type == NodeType.SHOP:
                        shop = True
                        
                    if route[i].node_type == NodeType.DEPOT:
                        depot = True
                            

                    if route[i].node_type == NodeType.TASK:
                        ### ! WORK COST
                        duration_workTask = tasks[route[i].id].duration
                        duration_work += duration_workTask

                        ### ! INCOME
                        incomeTech += tasks[route[i].id].income

                        self.task_costs[route[i].id] = (travel_minutes+duration_workTask)*self.data.technician_workHourCost + self.resourcesCost[tech_id] + cost_drive

                        
                
                resources = 0                
                restock = 0

                for resource_id, value in total_resourcesUsed.items():
                    resource = value[0]
                    if resource_id not in total_resourcesToRestock.keys():
                        restoc = 0
                    else:
                        restoc = total_resourcesToRestock[resource_id][0]

                    if value[0] - restoc > 0:
                        resources += self.data.resource_cost[resource_id] * (resource - restoc) 
                    else:
                        resources += self.data.resource_cost[resource_id] * (resource) 
                    
                    restock += self.data.resource_cost[resource_id] * restoc 
                    resources +=  restoc  


                if shop:
                    self.shopCost[tech_id] = restock * SHOP_COST_MULT
                elif depot:
                    self.depotCost[tech_id] = restock
                


                self.resourcesCost[tech_id] = resources + restock


                self.pathCost[tech_id] = cost_drive * self.data.drivingHourCost                  

                cost_work = duration_work * self.data.workHourCost
                cost_drive = (self.pathCost[tech_id] / self.data.drivingHourCost) * self.data.workHourCost
                self.timeCost[tech_id] = cost_drive + cost_work

                ######### ! WEATHER
                self.weatherExtraTime[tech_id] = weatherExtraTime
                self.weatherSafetyRiskKm[tech_id] = weatherSafetyRiskKm
                self.weatherCost[tech_id] = weatherCost
                ################

                cost_monetary += self.pathCost[tech_id]
                cost_monetary += self.timeCost[tech_id]
                cost_monetary += self.weatherCost[tech_id]
                cost_monetary += self.resourcesCost[tech_id]
                
                self.monetaryCost[tech_id] = cost_monetary

                self.income[tech_id] = incomeTech
                
                self.changedRoute[tech_id] = False
                

            
            totalPathCost += self.pathCost[tech_id]
            
            totalTimeCost += self.timeCost[tech_id]

            totalWeatherExtraTime += self.weatherExtraTime[tech_id]
            totalWeatherSafetyRiskKm += self.weatherSafetyRiskKm[tech_id]
            
            totalWeatherCost += self.weatherCost[tech_id]

            totalIncome += self.income[tech_id]
            

            totalShopCost += self.shopCost[tech_id]
            totalDepotCost += self.depotCost[tech_id]
            totalResourceCost += self.resourcesCost[tech_id]
        

        self.totalMonetaryCost = totalPathCost + totalTimeCost 
        self.totalPathCost = totalPathCost
        self.totalTimeCost = totalTimeCost

        self.totalWeatherExtraTime = totalWeatherExtraTime
        self.totalWeatherSafetyRiskKm = totalWeatherSafetyRiskKm
        self.totalWeatherCost = totalWeatherCost
        self.totalIncome = totalIncome
       
        self.totalShopCost = totalShopCost
        self.totalDepotCost = totalDepotCost

        self.totalResourceCost = totalResourceCost
        

        self.weight = self.totalMonetaryCost - self.totalIncome + self.forgottenTaskCost

        ### ! WEATHER
        self.totalMonetaryCost += totalWeatherCost


    def __str__(self):
        #print(f"Tasks in Solution: {self.tasks}")
        """
        masterID_list = []
        tech_id_list = []
        for master_id, route in self.routes.items():
            task_ids = [task.id for task in route]
            start = [task.start_time for task in route]
            end = [task.start_time for task in route]
            whole = 
            #master_id = self.master_ids[tech_id]
            masterID_list.append(f" \"{master_id}\": {task_ids}, {start}, {end}, ")
            #tech_id_list.append(f" \"{tech_id}\": {task_ids},")
            
        return  f"self.totalMonetaryCost" + "\n" + " ".join(masterID_list)
        """
        lines = []
        for master_id, route in self.routes.items():
            task_count = 0
            trip_lines = []

            for i, t in enumerate(route):

                # -----------------------
                # TECH
                # -----------------------
                if t.node_type == NodeType.TECH:
                    line = f'    [TECH] id={t.id} | {t.start_time}'
                    trip_lines.append(line)
                    continue

                # -----------------------
                # DEPOT
                # -----------------------
                if t.node_type == NodeType.DEPOT:
                    line = f'    [DEPOT] id={t.id} | {t.start_time} → {t.end_time}  | '
                    trip_lines.append(line)
                    continue

                # -----------------------
                # SHOP
                # -----------------------
                if t.node_type == NodeType.SHOP:
                    line = f'    [SHOP] id={t.id} | {t.start_time} → {t.end_time}  |'
                    trip_lines.append(line)
                    continue

                # -----------------------
                # TASK
                # -----------------------
                if t.node_type == NodeType.TASK:
                    task = self.tasks[t.id]

                    start_ok = task.start_tw <= t.start_time <= task.end_tw
                    end_ok = task.start_tw <= t.end_time <= task.end_tw

                    if start_ok and end_ok:
                        status = "OK"
                    else:
                        reasons = []
                        if not start_ok:
                            reasons.append("START")
                        if not end_ok:
                            reasons.append("END")
                        status = "VIOLATION(" + ",".join(reasons) + ")"

                    # -----------------------
                    # REAL ROUTE INTEGRITY CHECKS
                    # -----------------------

                    # ordering check (critical for your bug)
                    if i > 0:
                        prev = route[i - 1]
                        if t.start_time < prev.end_time:
                            status += " | ORDER-VIOLATION"

                    # cross-day anomaly detection
                    if t.start_time.date() != t.end_time.date():
                        status += " | CROSS-DAY"

                    line = (
                        f'    [TASK] id={t.id} | {t.start_time} → {t.end_time} | '
                        f'TW=({task.start_tw} → {task.end_tw}) | {status}'
                    )

                    trip_lines.append(line)
                    task_count += 1  # Increment task count

            trip_lines.append(f'    [INFO] Total tasks in route: {task_count}')

            route_str = f'"{master_id}":\n' + "\n".join(trip_lines)
            lines.append(str(route_str))
            info = []
            info.append("self.totalMonetaryCost:        " + str(self.totalMonetaryCost))
            info.append("self.totalPathCost:            " + str(self.totalPathCost))
            info.append("self.totalTimeCost:            " + str(self.totalTimeCost))

            info.append("self.totalWeatherExtraTime:    " + str(self.totalWeatherExtraTime))
            info.append("self.totalWeatherSafetyRiskKm: " + str(self.totalWeatherSafetyRiskKm))
            info.append("self.totalWeatherCost:         " + str(self.totalWeatherCost))

            info.append("self.shopCost:                 " + str(self.totalShopCost))
            info.append("self.depotCost:                " + str(self.totalDepotCost))
            info.append("self.totalResourceCost:        " + str(self.totalResourceCost))
            
            info.append("self.totalIncome:              " + str(self.totalIncome))
            info.append("self.forgottenTaskCost:        " + str(self.forgottenTaskCost))
            info.append("self.weight:                   " + str(self.weight))
        
        
        return "\n\n".join(lines) + "\n".join(info)

        
    """

    """     


class Operators: 
    def __init__(self):
        self.destroy_ops = Destroy_Operator()
        self.repair_ops = Repair_Operator()
        
        self.chosen_destroy = 0
        self.chosen_repair = 2

        self.weights_destroy = [1.0] * 5
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
    

    def destroy(self, solution, unassigned_tasks, tasks, relatedness):
        #self.chosen_destroy = 0
        """if self.chosen_destroy == 3:
            self.chosen_destroy = 0
        if self.chosen_destroy == 4:
            self.chosen_destroy = 1
        if self.chosen_destroy == 5:
            self.chosen_destroy = 2
        self.chosen_destroy = 3
        #print(self.chosen_destroy)"""
        #self.chosen_destroy = 3
        print("destroyer: ", self.chosen_destroy)
        #if self.chosen_destroy == 1:
        #    self.chosen_destroy = 4
        match self.chosen_destroy:
            case 0:
                return self.destroy_ops.random(solution, unassigned_tasks)
            case 1:
                return self.destroy_ops.route(solution, unassigned_tasks) # ! SOMETHING
            case 2:
                return self.destroy_ops.critical(solution, unassigned_tasks) #! after a while does nothing (no change at all, no randomness) !!!!
            case 3:
                return self.destroy_ops.shaw(solution, unassigned_tasks,relatedness)
            case 4:
                return self.destroy_ops.skill(solution, unassigned_tasks, tasks)
            #case 5:
            #    return self.destroy_ops.type(solution, unassigned_tasks)
            

    def repair(self, solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes,weather):
        #if self.chosen_repair == 2:
        #self.chosen_repair = 0
        match self.chosen_repair:
            case 0:
                return self.repair_ops.greedy(solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes,weather)
            case 1:
                return self.repair_ops.regret(solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes,weather)
            case 2:
                return self.repair_ops.random(solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes,weather)


    def renew_weights(self, score):
        self.score = score
        self.weights_destroy[self.chosen_destroy] = round((1.0 - self.reaction) * self.weights_destroy[self.chosen_destroy] + self.reaction * self.score,3)
        self.weights_repair[self.chosen_repair] = round((1.0 - self.reaction) * self.weights_repair[self.chosen_repair] + self.reaction * self.score,3)
        
    def updateScore(self,new_score):
        self.score = new_score

        def __str__(self):
            pass


class Destroy_Operator: 
    def __init__(self):
        pass
    

    def random(self, solution, unassigned_tasks): #k should be 10% of all nodes (but why?)
        new_solution = solution.copy()

        all_nodes = [
        (tech_id, node)
        for tech_id, route in new_solution.routes.items()
        for node in route
        if node.node_type == NodeType.TASK
        ]

        k = int(max(1, len(all_nodes) * 0.1))
        if not all_nodes:
            return new_solution, unassigned_tasks
        removed_nodes = random.sample(all_nodes, k)
        copied_nodes = set()
        print()
        print()

        for tech_id, node in removed_nodes:
            #if not new_solution.changedRoute[tech_id]:
            if tech_id not in copied_nodes:
                new_solution.routes[tech_id] = solution.routes[tech_id].copy()
                copied_nodes.add(tech_id)
            if node.node_type != NodeType.TASK:
                continue
            new_solution.routes[tech_id].remove(node)
            unassigned_tasks.append(node)
            print(node)

            new_solution.changedRoute[tech_id] = True

        return new_solution, unassigned_tasks


    def route(self,solution, unassigned_tasks):
        new_solution = solution.copy()

        all_routes = [
        (tech_id, route)
        for tech_id, route in solution.routes.items()
        ]

        k = int(max(1, len(all_routes) * 0.1))
        if not all_routes:
            return new_solution, unassigned_tasks
        removed_nodes = random.sample(all_routes, k)
        copied_routes = set()

        for tech_id, route in removed_nodes:
            if tech_id not in copied_routes:
                new_solution.routes[tech_id] = solution.routes[tech_id].copy()
                copied_routes.add(tech_id)
        
            new_solution.routes[tech_id] = [node for node in route if node.node_type == NodeType.TECH]

            for node in route:
                if node.node_type == NodeType.TASK:
                    unassigned_tasks.append(node)

            new_solution.changedRoute[tech_id] = True


        return new_solution, unassigned_tasks
    

    def critical(self,solution, unassigned_tasks):
        new_solution = solution.copy()

        all_nodes = [
        (tech_id, node)
        for tech_id, route in new_solution.routes.items()
        for node in route
        if node.node_type == NodeType.TASK
        ]

        
        sorted_costs = sorted(new_solution.task_costs.items(), key=lambda x: x[1], reverse=True)

        k = int(max(1, len(sorted_costs) * 0.1))
        if not all_nodes:
            return new_solution, unassigned_tasks
        expensive_tasks = [task_id for task_id, cost in sorted_costs[:k]]
        copied_tasks = set()

        for tech_id, node in all_nodes:
            if node.id in expensive_tasks:
                if node.node_type != NodeType.TASK:
                    continue
                #if not new_solution.changedRoute[tech_id]:
                if tech_id not in copied_tasks:
                    new_solution.routes[tech_id] = solution.routes[tech_id].copy()
                    copied_tasks.add(tech_id)

                new_solution.routes[tech_id].remove(node)
                unassigned_tasks.append(node)

                new_solution.changedRoute[tech_id] = True


        return new_solution, unassigned_tasks
    


    def shaw(self,solution, unassigned_tasks, relateddness): ### needs relatedness
        #! Travel time, duration, time window and penalty are used to define
        #! task-relatedness. The most related tasks are unassigned 
        #* extra resources and skills 
        
        new_solution = solution.copy()

        k = int(len(relateddness)*0.1)
        removed_count = 0
        removed_tasks = False
        removed_task_ids = set()
        for (task_1, task_2), value in relateddness.items():
            
            if removed_count >= k:
                removed_tasks = True
                break
            task_1_is_found = False
            task_2_is_found = False

            tech_id_1 = 0
            node_id_1 = None
            tech_id_2 = 0
            node_id_2 = None
            for tech_master_id, route in new_solution.routes.items():
                
                for node in route:
                    if node.node_type != NodeType.TASK:
                        continue
                    if task_1 == node.id:
                        task_1_is_found = True
                        tech_id_1 = tech_master_id
                        node_id_1 = node
                    if task_2 == node.id:
                        task_2_is_found = True
                        tech_id_2 = tech_master_id
                        node_id_2 = node
                    
                if task_1_is_found and task_2_is_found:
                    break
                
            if not task_2_is_found or not task_1_is_found:
                continue


            if not new_solution.changedRoute[tech_id_1]:
                new_solution.routes[tech_id_1] = solution.routes[tech_id_1].copy()
                new_solution.changedRoute[tech_id_1] = True

            if not new_solution.changedRoute[tech_id_2]:
                new_solution.routes[tech_id_2] = solution.routes[tech_id_2].copy()
                new_solution.changedRoute[tech_id_2] = True


            if node_id_1.id not in removed_task_ids:
                if node_id_1 in new_solution.routes[tech_id_1]:
                    new_solution.routes[tech_id_1].remove(node_id_1)

                unassigned_tasks.append(node_id_1)
                removed_task_ids.add(node_id_1.id)



            if node_id_2.id not in removed_task_ids:
                if node_id_2 in new_solution.routes[tech_id_2]:
                    new_solution.routes[tech_id_2].remove(node_id_2)

                unassigned_tasks.append(node_id_2)
                removed_task_ids.add(node_id_2.id)

            removed_count += 1


            """if task_1_is_found and task_2_is_found:
                new_solution.routes[tech_id_1].remove(node_id_1)
                new_solution.routes[tech_id_2].remove(node_id_2)
                unassigned_tasks.append(node_id_1)
                unassigned_tasks.append(node_id_2)
                print(node_id_2)
                removed_count += 1
                new_solution.changedRoute[tech_id_1] = True
                new_solution.changedRoute[tech_id_2] = True"""
            
        
        #print(unassigned_tasks)
        return new_solution, unassigned_tasks
    

    def skill(self, solution, unassigned_tasks, tasks): ### ! not finished
        new_solution = solution.copy()

        all_nodes = [
        (tech_id, node)
        for tech_id, route in new_solution.routes.items()
            for node in route
                if node.node_type == NodeType.TASK
        ]
        if not all_nodes:
            return new_solution, unassigned_tasks
        #print(solution)
        #print(all_nodes)
        skills_set = set()
        for tech_id, node in all_nodes:
            print(node)
            skills_set.update(tasks[node.id].skills)

        skills = []
        for skill in skills_set:
            skills.append(skill)

        k = int(max(1, len(skills) * 0.1))
        #print(k)
        #print(skills)
        chosen_skills = random.sample(skills, k)
        k_tasks = int(max(1, len(all_nodes) * 0.05))
        

        coped_tasks = set()
        for skill in chosen_skills:
            removed_task_count = 0
            for tech_id, node in all_nodes:
                if node.node_type != NodeType.TASK:
                    continue
                if removed_task_count == k_tasks:
                    break
                current_task = tasks[node.id]
                if skill in current_task.skills:
                    #if not new_solution.changedRoute[tech_id]:
                    if tech_id not in coped_tasks:
                        new_solution.routes[tech_id] = solution.routes[tech_id].copy()
                        coped_tasks.add(tech_id)

                    new_solution.routes[tech_id].remove(node)
                    unassigned_tasks.append(node)

                    new_solution.changedRoute[tech_id] = True
                    removed_task_count+=1   


        return new_solution, unassigned_tasks
    

    def type(self,solution, unassigned_tasks): ### needs types # don't have types unless skills and resources is a type
        new_solution = solution.copy()

        return new_solution, unassigned_tasks  
        

    def __str__(self):
        pass


class Repair_Operator: 
    def __init__(self):
        pass

    def calculateRouteCost(self,  route, distances, tasks, data, weather, tech): #start, end, id,
        totatTravel = 0.0
        resource_cost_total = 0.0
        totalTime = 0.0
        income = 0.0
        shop = False
        depot = False
        weatherCost = 0.0
        total_resourcesUsed = {}
        total_resourcesToRestock = {}
        currentNode = 0.0
        needed_toRestock = False
        currentNode = 0.0
        firstResourceFailurePoint = -1
        cost_monetary = 0.0

        duration_work = 0.0
        cost_drive = 0.0

        weatherExtraTime = 0.0
        weatherSafetyRiskKm = 0.0
        weatherCost = 0.0
        duration_workTask = 0.0
        incomeTech = 0.0

        resourceCost = 0.0
        travel_minutes = 0.0

        for i in range(len(route)-2):
            if route[i].node_type == NodeType.TECH and route[i+1] == NodeType.TECH:
                continue
            
            if route[i].node_type in [NodeType.SHOP, NodeType.DEPOT]:
                totalTime += (route[i].end_time-route[i].start_time).total_seconds() *60
            
            if route[i].node_type == NodeType.TASK:
                ### ! WORK COST
                duration_workTask = tasks[route[i].id].duration

                ### ! INCOME
                incomeTech += tasks[route[i].id].income

                for resource_id in tasks[route[i].id].resources:
                    if resource_id not in total_resourcesUsed:
                        total_resourcesUsed[resource_id] = [0, 0.0] 

                    total_resourcesUsed[resource_id][0] += 1 # saves resouce count needed
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

            if route[i].node_type == NodeType.DEPOT:
                depot = True

            if route[i].node_type == NodeType.SHOP:
                shop = True

            current_tech_position = Distance_Node(route[i].node_type, route[i].id)
            next_route_position =  Distance_Node(route[i+1].node_type, route[i+1].id)
            km, travel = distances.get_distance(current_tech_position,next_route_position)

            #print(travel)
            totatTravel += travel
            if WEATHER_TEST:
                ### ! WEATHER assign
                cost_factor, slow_downFactor = distances.get_weather(current_tech_position, next_route_position, 
                                        route[i].end_time, route[i].end_time+datetime.timedelta(minutes=travel),
                                        weather)
                
                weatherExtraTime = travel * slow_downFactor - travel
                weatherSafetyRiskKm = km * cost_factor
                weatherCost = weatherExtraTime * (data.technician_workHourCost + data.drivingHourCost) + weatherSafetyRiskKm
                #weatherCost += (travel*slow_downFactor-travel) * (data.technician_workHourCost + data.drivingHourCost + cost_factor) 
            
            totalTime += duration_workTask
        resources = 0                
        restock = 0
        for resource_id, value in total_resourcesUsed.items():
            resource = value[0]
            if resource_id not in total_resourcesToRestock.keys():
                restoc = 0
            else:
                restoc = total_resourcesToRestock[resource_id][0]

            if value[0] - restoc > 0:
                resources += data.resource_cost[resource_id] * (resource - restoc) 
            else:
                resources += data.resource_cost[resource_id] * (resource) 
            
            restock += data.resource_cost[resource_id] * restoc 
            resources +=  restoc  

        if shop:
            restock = restock * SHOP_COST_MULT
        elif depot:
            restock = restock

        resource_cost_total + restock + resources
        totalMonetaryCost = + (totatTravel + totalTime)*data.workHourCost + totatTravel*data.drivingHourCost
        if WEATHER_TEST:
            totalMonetaryCost += weatherCost





        return totalMonetaryCost - income

    def assign_feasability(self, task, tech, distances): # skills and time_windows
        can_assign = True
        
        for skill in task.skills:
            if not (skill in tech.skills):
                return not can_assign
            
        return can_assign
        """
        travel_time = distances.get_distance(Distance_Node(NodeType.TECH,tech.master_id),Distance_Node(NodeType.TASK,task.id))
        travel_time_home = distances.get_distance(Distance_Node(NodeType.TASK,task.id),Distance_Node(NodeType.TECH,tech.master_id))
        for i in range(len(tech.start_tw)):
            
            tech_arrives_before_end_of_task = tech.start_tw[i] + datetime.timedelta(minutes=travel_time) + datetime.timedelta(minutes=task.duration)
            if  tech_arrives_before_end_of_task > task.end_tw + TASK_OVERTIME:
                #print(tech_arrives_before_end_of_task, task.end_tw + TASK_OVERTIME)
                continue
            
            task_starts_before_end_of_work_shift = task.start_tw +  datetime.timedelta(minutes=task.duration)+ datetime.timedelta(minutes=travel_time_home) 
            if  task_starts_before_end_of_work_shift > tech.end_tw[i] + TECH_OVERTIME:
                #print(task_starts_before_end_of_work_shift, tech.end_tw[i] + TECH_OVERTIME)
                continue

            #print()
            #print("proper start: ", tech_arrives_before_end_of_task, task.end_tw + TASK_OVERTIME)
            #print("proper end: ", task_starts_before_end_of_work_shift, tech.end_tw[i] + TECH_OVERTIME )
            break
        """
        


    def timeWindow_feasabilityTECH(self, nodes, tech, distances, tasks):
        
        
        node_0 = Distance_Node(nodes[0].node_type, nodes[0].id)
        node_1 = Distance_Node(nodes[1].node_type, nodes[1].id)
        node_2 = Distance_Node(nodes[2].node_type, nodes[2].id)

        if nodes[0].node_type == NodeType.TASK:
            start_time_0 = tasks[nodes[0].id].start_tw
            duration_0 = datetime.timedelta(minutes=tasks[nodes[0].id].duration) + TECH_REST
        
        else:
            start_time_0 = nodes[0].start_time
            duration_0 = datetime.timedelta(minutes=0)

        km, travelTime0_1 = distances.get_distance(node_0, node_1)


        if nodes[1].node_type == NodeType.TASK:
            end_tw_1 = tasks[nodes[1].id].end_tw
            duration_1 = tasks[nodes[1].id].duration

        elif nodes[1].node_type == NodeType.DEPOT:
            end_tw_1 = tasks[nodes[1].id].end_tw
            duration_1 = 30

        elif nodes[1].node_type == NodeType.SHOP:
            end_tw_1 = tasks[nodes[1].id].end_tw
            duration_1 = 10


        travelTime0_1 = datetime.timedelta(minutes=travelTime0_1)
        duration_1 = datetime.timedelta(minutes=duration_1)


        if start_time_0 + duration_0 + travelTime0_1 + duration_1 <= end_tw_1 + TASK_OVERTIME:
            pass
        else:
            return False

            
        km, travelTime1_2 = distances.get_distance(node_1, node_2)


        travelTime1_2 = datetime.timedelta(minutes=travelTime1_2)

        if nodes[2].node_type == NodeType.TASK:
            end_tw_2 = tasks[nodes[2].id].end_tw
            duration_2 = datetime.timedelta(minutes=(tasks[nodes[2].id].duration)) + TECH_REST
            end_tw_2 + TASK_OVERTIME
        
        else:
            end_tw_2 = nodes[2].end_time
            duration_2 = datetime.timedelta(minutes=0)
            end_tw_2 + TECH_OVERTIME
            
            

        if end_tw_1 + duration_1 + travelTime1_2 + duration_2 <= end_tw_2:
            return True


        return False

    def timeWindow_feasability(self, nodes, tech, distances, tasks):
        for i in range(len(tech.start_tw)):
            #print("timeWindowFeasability" , i)
            node_0 = Distance_Node(nodes[0].node_type, nodes[0].id)
            node_1 = Distance_Node(nodes[1].node_type, nodes[1].id)
            node_2 = Distance_Node(nodes[2].node_type, nodes[2].id)
            if nodes[0].node_type == NodeType.TASK:
                start_time_0 = tasks[nodes[0].id].start_tw
                duration_0 = datetime.timedelta(minutes=tasks[nodes[0].id].duration) + TECH_REST
            
            else:
                start_time_0 = tech.start_tw[i]
                duration_0 = datetime.timedelta(minutes=0)

            km, travelTime0_1 = distances.get_distance(node_0, node_1)

            weather_travel = 0

            end_tw_1 = tasks[nodes[1].id].end_tw
            duration_1 = tasks[nodes[1].id].duration

            
            travelTime0_1 = datetime.timedelta(minutes=travelTime0_1)
            duration_1 = datetime.timedelta(minutes=duration_1)

            if start_time_0 + duration_0 + travelTime0_1 + duration_1 <= end_tw_1 + TASK_OVERTIME:
                pass
            else:
                continue
            
            km, travelTime1_2 = distances.get_distance(node_1, node_2)
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
    
    def insertionStartDurationEnd(self, insertion_node, task, end_task, travel_end_to_insertion):
        insertion_node_start = datetime.timedelta(minutes=0)
        insertion_duration = datetime.timedelta(minutes=0)
        insertion_node_end = datetime.timedelta(minutes=0)
        insertion_overtime = datetime.timedelta(minutes=0)
        travel_end_to_insertion = datetime.timedelta(minutes=travel_end_to_insertion)

        if insertion_node.node_type is NodeType.TASK:
            insertion_node_start = max(end_task + travel_end_to_insertion, task[insertion_node.id].start_tw) # *
            insertion_duration = datetime.timedelta(minutes=int(task[insertion_node.id].duration)) # *
            insertion_node_end = insertion_node_start + insertion_duration # * overtime?
            #print(insertion_node_end, task.end_tw)
            insertion_overtime =  insertion_node_end - task[insertion_node.id].end_tw
            #print(insertion_overtime > TASK_OVERTIME)
            
        elif insertion_node.node_type is NodeType.SHOP:
            insertion_node_start = end_task + travel_end_to_insertion
            insertion_duration = SHOP_DURATION
            insertion_node_end = insertion_node_start + insertion_duration
            
        elif insertion_node.node_type is NodeType.DEPOT:
            insertion_node_start = end_task + travel_end_to_insertion
            insertion_duration = DEPOT_DURATION
            insertion_node_end = insertion_node_start + insertion_duration

        return insertion_node_start, insertion_duration, insertion_node_end, insertion_overtime
    

    def timeFeasability(self,insertion_overtime, prev_nodes,insertion_node_end,travel_insertion_to_next,next_nodes,insertion_node_start,start_next_node,end_task, insertion_node):
        feasable = True
        feasability_reason = ""
        if insertion_overtime > TASK_OVERTIME:
            feasable = False
        if prev_nodes[-1].end_time.time() >= datetime.time(16, 0):
            
            if (insertion_node_end + travel_insertion_to_next).time() > datetime.time(17, 0):
                feasable = False
            elif (insertion_node_end + travel_insertion_to_next).time() < datetime.time(16, 0):
                feasable = False
            if insertion_node.node_type in [NodeType.SHOP, NodeType.DEPOT]:
                feasable = False

            #print((insertion_node_end + travel_insertion_to_next).time())
            #print((insertion_node_end + travel_insertion_to_next).time() > datetime.time(17, 0))
        if  prev_nodes[-1].end_time.date() != next_nodes[0].start_time.date() and next_nodes[0].node_type != NodeType.TECH:
            return feasability_reason, False

        if  prev_nodes[-1].start_time.date() == next_nodes[0].start_time.date():
            if insertion_node_start.date() != prev_nodes[-1].end_time.date():
                feasable = False
            # prev 400-500
            # insertino 600-800
            # next 900-1000
            #! insert before next task starts

            #if next_nodes[0].node_type == NodeType.TECH:
            if (insertion_node_end + travel_insertion_to_next+TECH_REST) >= (start_next_node): # 800 < 900
                feasability_reason = "arrives after start of next node"
                feasable = False
            if (insertion_node_start+TECH_REST) >= (start_next_node): # 600 < 900
                feasability_reason = "starts after next node"
                feasable = False
            #if prev_nodes[-1].node_type == NodeType.TECH:
            if (insertion_node_end + travel_insertion_to_next-TECH_REST) <= (end_task): # 800 > 500
                feasable = False
            #! insert after previous task ends
            if (insertion_node_start+TECH_REST) <= (end_task): # 600 > 500
                feasable = False
        
        if  prev_nodes[-1].start_time.date() != next_nodes[0].start_time.date():
            if prev_nodes[-1].start_time.time() < datetime.time(15, 0):
                feasable = False
                feasability_reason = ""

        return feasability_reason, feasable


    #if insertion_node.id in [61,62,65,169,16,170,168]:
    #    return [], False

    #if prev_nodes[-1].node_type != NodeType.TECH and next_nodes[0].node_type != NodeType.TECH:
            #print(end_task.time(), insertion_node_start.time(), insertion_node_end.time(), start_next_node.time(), end_task.time() < insertion_node_start.time(), insertion_node_end.time() < start_next_node.time(), insertion_node_end.date(), start_next_node.date())
    #        if not (end_task.time() < insertion_node_start.time()) or not(insertion_node_end.time() < start_next_node.time()):
                #print(end_task.time(), insertion_node_start.time(), insertion_node_end.time(), start_next_node.time(), end_task.time() < insertion_node_start.time(), insertion_node_end.time() < start_next_node.time(), insertion_node_end.date(), start_next_node.date())
    #            pass
        #print()
        #insertion_node.start_time = insertion_node_start
        #insertion_node.end_time = insertion_node_end
    #! in full rebuild after building the route up to new insertion could just stop if next step can be done
    #printing = True
    #    prev =  len(prev_nodes)-1
    #    next =  len(prev_nodes)+1

        """for i in range(len(new_route)-2):
            if new_route[i].id in [61,62,63,60,65]:

            if  new_route[i].node_type != NodeType.TECH and new_route[i+1].node_type != NodeType.TECH:
                if  new_route[i].end_time > new_route[i+1].start_time:
                    print(new_route[i].end_time > new_route[i+1].start_time)
                    print(new_route[i].end_time, new_route[i+1].start_time)
                    return [], False
            
            """
        
        """if tech.master_id == 35:
        #if printing:
            #if (new_route[prev].node_type == NodeType.TASK or new_route[next].node_type == NodeType.TASK) or (new_route[prev].node_type == NodeType.TASK and new_route[next].node_type == NodeType.TASK):
            #if new_route[prev].end_time > insertion_node.start_time or insertion_node.end_time > new_route[next].start_time: 
                
            if insertion_node.id in [61]: #and (prev_nodes[-1] in [61,62,63,60,65] or next_nodes[0] in [61,62,63,60,65]):
                #if (new_route[prev].start_time- insertion_node_start).total_seconds() <300 and (new_route[prev].start_time- insertion_node_start).total_seconds() > -301:
                    #print((new_route[prev].start_time- insertion_node_start).total_seconds())
                #for node in new_route:
                #    if node.node_type == NodeType.TASK:
                #        print("AAAAAAAAA: ", node.node_type, node.id, node.start_time, node.end_time)
                #    else:
                #        print(node.node_type, node.id, node.start_time, node.end_time)
                
                
                print(prev_nodes[-1].id, insertion_node.id, new_route[next].id, end_task.time(), insertion_node_start.time(), insertion_node_end.time(), start_next_node.time(), end_task.time() < insertion_node_start.time(), insertion_node_end.time() < start_next_node.time(), insertion_node_end.date(), start_next_node.date())
                print(new_route[prev].id, insertion_node.id, new_route[next].id, new_route[prev].end_time.time(), insertion_node_start.time(), insertion_node_end.time(), new_route[next].start_time.time(), new_route[next].end_time.time() < insertion_node_start.time(), insertion_node_end.time() < new_route[next].start_time.time(), insertion_node_end.date(), new_route[next].start_time.date())
                print()
            
            #print()
            if end_task.time() > datetime.time(7, 15) and start_next_node.time() < datetime.time(16, 0) and end_task.time() != datetime.time(16, 00) and start_next_node.time() != datetime.time(7, 15):
            #if not (end_task.time() < insertion_node_start.time()) or not(insertion_node_end.time() < start_next_node.time()):
            #print(end_task.time(), insertion_node_start.time(), insertion_node_end.time(), start_next_node.time(), end_task.time() < insertion_node_start.time(), insertion_node_end.time() < start_next_node.time(), insertion_node_end.date(), start_next_node.date())
                pass
            if insertion_node_start.time() == datetime.time(7, 30):
                #print(prev_nodes[-1].id, insertion_node.id, next_nodes[-1].id, end_task.time(), insertion_node_start.time(), insertion_node_end.time(), start_next_node.time(), end_task.time() < insertion_node_start.time(), insertion_node_end.time() < start_next_node.time(), insertion_node_end.date(), start_next_node.date())
                pass

        """
         #if insertion_node_start > prev_nodes[last_prev_node].end_time:
        #    if insertion_node_end + travel_insertion_to_next < start_next_node:
                #if next_nodes[0].node_type != NodeType.TECH:
                #    if insertion_node_start < prev_nodes[-1].end_time:
                #        if insertion_node_start.date() == prev_nodes[-1].end_time.date():
                
            
        #return [], False

    def one_nodeInsertion(self, prev_nodes, insertion_node, next_nodes, tech, tasks, distances, weather):
        
        last_prev_node = len(prev_nodes)-1
        
        #if prev_nodes[-1].node_type == NodeType.TECH and prev_nodes[-1].end_time.time() == datetime.time(16, 0):
        #    end_task = prev_nodes[-2].end_time
        #    travel_end_to_insertion = distances.get_distance(Distance_Node(prev_nodes[-2].node_type, prev_nodes[-2].id), Distance_Node(insertion_node.node_type, insertion_node.id))
        #    
        #else:
        end_task = prev_nodes[last_prev_node].end_time
        km, travel_end_to_insertion = distances.get_distance(Distance_Node(prev_nodes[-1].node_type, prev_nodes[-1].id), Distance_Node(insertion_node.node_type, insertion_node.id))
        if WEATHER_TEST:
            current_tech_position = Distance_Node(prev_nodes[-1].node_type, prev_nodes[-1].id)
            next_route_position = Distance_Node(insertion_node.node_type, insertion_node.id)
            travel_start = end_task
            travel_end = travel_start + datetime.timedelta(minutes=travel_end_to_insertion)
            
            cost_factor, slow_downFactor = distances.get_weather(current_tech_position, next_route_position, travel_start, travel_end, weather)
            weatherExtraTime = travel_end_to_insertion * slow_downFactor - travel_end_to_insertion
            weather_travel = travel_end_to_insertion + weatherExtraTime
            #weather_travel = datetime.timedelta(minutes=weather_travel)
            insertion_node_start, insertion_duration, insertion_node_end, insertion_overtime = self.insertionStartDurationEnd(insertion_node, tasks, end_task, weather_travel)
        else:
            #travel_end_to_insertion = distances.get_distance(Distance_Node(prev_nodes[-1].node_type, prev_nodes[-1].id), Distance_Node(insertion_node.node_type, insertion_node.id))
        
            insertion_node_start, insertion_duration, insertion_node_end, insertion_overtime = self.insertionStartDurationEnd(insertion_node, tasks, end_task, travel_end_to_insertion)

        insertion_node_start, insertion_duration, insertion_node_end, insertion_overtime = self.insertionStartDurationEnd(insertion_node, tasks, end_task, travel_end_to_insertion)
        km, travel_insertion_to_next = distances.get_distance(Distance_Node(insertion_node.node_type, insertion_node.id),Distance_Node(next_nodes[0].node_type, next_nodes[0].id))
        travel_insertion_to_next = datetime.timedelta(minutes=travel_insertion_to_next)
        start_next_node = next_nodes[0].start_time
        #if prev_nodes[-1].node_type == NodeType.TECH and prev_nodes[-1].end_time.time() == datetime.time(16, 0):
        #    feasable = self.timeFeasability(insertion_overtime, [prev_nodes[-1]],insertion_node_end,travel_insertion_to_next,next_nodes,insertion_node_start,start_next_node,end_task)
        #else:
        feasability_reason, feasable = self.timeFeasability(insertion_overtime, prev_nodes,insertion_node_end,travel_insertion_to_next,next_nodes,insertion_node_start,start_next_node,end_task, insertion_node)

        if not feasable:
            return feasability_reason, None, [], False

            
        new_node = Route_Node(insertion_node.node_type, insertion_node.id, insertion_node_start, insertion_node_end)
        new_route = prev_nodes + [insertion_node] + next_nodes
        

        return "", new_node, new_route, True
        

       

    # * where it gets the end? #! what if it is TECH node, that does not have end time # * tech end has end_time whihc is start of tw
    # tech 1600
    # tech 0730
    # task ?
    # task ? 
    #if prev_nodes[-1].start_time < tasks[insertion_node.id].end_tw and tasks[insertion_node.id].end_tw < next_nodes[0].start_time: # !!!!!!!!!!
    #    print(prev_nodes[-1].start_time, tasks[insertion_node.id].end_tw, next_nodes[0].start_time)
   
    ### ! i do use the newly inserted route, hwoever it has no start or end...
    ### ! inserted goes further and tries to rebuild whihc is fine.
    ### ! do both shop and task insertion at same time
    ### ! update technician resources
    ### ! what if technician goes to depo/shop in his free time windwo and nothing else in that day prep for next day?

    # ! add weather
    # * all technician homes from and to are inserted at construction
    # ! SHOP AND DEPOT does not have time_window
    #if prev_nodes[last_prev_node].start_time < insertion_node_end and insertion_node_start < prev_nodes[last_prev_node].end_time:
    #    return None, [], False
    
    #if next_nodes[0].start_time < insertion_node_start or insertion_node_end > next_nodes[0].end_time: #and insertion_node_start < next_nodes[0].end_time:
    #    return None, [], False
    def insertion_feasability(self, prev_nodes, insertion_node, next_nodes, tech, tasks, distances, weather):
        last_prev_node = len(prev_nodes)-1
        feasability = ""
        #print(last_prev_node)
        #print(prev_nodes)
        if not prev_nodes:
            feasability = "empty prev nodes"
            return feasability, None, [], False
        
        #if prev_nodes[last_prev_node].node_type == NodeType.TECH and prev_nodes[last_prev_node].end_time.time() == datetime.time(16, 0):
        #    end_task = prev_nodes[last_prev_node-1].end_time
        #    travel_end_to_insertion = distances.get_distance(Distance_Node(prev_nodes[last_prev_node-1].node_type, prev_nodes[last_prev_node-1].id), Distance_Node(insertion_node.node_type, insertion_node.id))
        #    
        #else:
        end_task = prev_nodes[last_prev_node].end_time 
        km, travel_end_to_insertion = distances.get_distance(Distance_Node(prev_nodes[-1].node_type, prev_nodes[-1].id), Distance_Node(insertion_node.node_type, insertion_node.id))
        insertion_node_start = None
        insertion_duration = None
        insertion_node_end = None
        insertion_overtime = None

        if WEATHER_TEST:
            current_tech_position = Distance_Node(prev_nodes[-1].node_type, prev_nodes[-1].id)
            next_route_position = Distance_Node(insertion_node.node_type, insertion_node.id)
            travel_start = end_task
            travel_end = travel_start + datetime.timedelta(minutes=travel_end_to_insertion)
            
            cost_factor, slow_downFactor = distances.get_weather(current_tech_position, next_route_position, travel_start, travel_end, weather)
            weatherExtraTime = travel_end_to_insertion * slow_downFactor - travel_end_to_insertion
            weather_travel = travel_end_to_insertion + weatherExtraTime
            #weather_travel = datetime.timedelta(minutes=weather_travel)
            insertion_node_start, insertion_duration, insertion_node_end, insertion_overtime = self.insertionStartDurationEnd(insertion_node, tasks, end_task, weather_travel)
        else:
            #travel_end_to_insertion = distances.get_distance(Distance_Node(prev_nodes[-1].node_type, prev_nodes[-1].id), Distance_Node(insertion_node.node_type, insertion_node.id))
        
            insertion_node_start, insertion_duration, insertion_node_end, insertion_overtime = self.insertionStartDurationEnd(insertion_node, tasks, end_task, travel_end_to_insertion)

        km, travel_insertion_to_next = distances.get_distance(Distance_Node(insertion_node.node_type, insertion_node.id),Distance_Node(next_nodes[0].node_type, next_nodes[0].id))
        travel_insertion_to_next = datetime.timedelta(minutes=travel_insertion_to_next)
        if next_nodes[0].start_time is None:
            next_nodes[0].start_time = max(insertion_node_end + travel_insertion_to_next+ TECH_REST, tasks[next_nodes[0].id].start_tw)
            next_nodes[0].end_time = tasks[next_nodes[0].id].end_tw+TASK_OVERTIME

            if insertion_node_end + TECH_REST+ travel_insertion_to_next + datetime.timedelta(minutes=tasks[next_nodes[0].id].duration) > next_nodes[0].end_time:
                return feasability, None, [], False

        #if insertion_overtime > TASK_OVERTIME:
        #    return None, [], False
        
        next_task_start_feasability = None

        indx = 0 
        if next_nodes[indx].node_type is NodeType.SHOP or next_nodes[indx].node_type is NodeType.DEPOT:
            indx = 1
        if next_nodes[indx].node_type is NodeType.TECH: # depends if it is last node or not or maybe just should somehow work with this in a different way
            next_task_start_feasability = next_nodes[indx].start_time + TECH_OVERTIME
            if insertion_node_end - next_nodes[indx].start_time > TECH_OVERTIME:
                return feasability,None, [], False
        elif next_nodes[indx].node_type is NodeType.TASK:
            next_task_start_feasability = tasks[next_nodes[indx].id].end_tw + TASK_OVERTIME
            next_task_duration = tasks[next_nodes[indx].id].duration 
            next_task_duration = datetime.timedelta(minutes=next_task_duration)

        if next_task_start_feasability is None:
            return feasability,None, [], False
        # ! add weather 
        
        feasability, feasable = self.timeFeasability(insertion_overtime, prev_nodes,insertion_node_end,travel_insertion_to_next,next_nodes,insertion_node_start,next_task_start_feasability,end_task, insertion_node)
        
        if not feasable:
            return feasability,None, [], False

                
       
        # ! building route not checking
        #if insertion_node_start > prev_nodes[last_prev_node].end_time:
        
        new_node = Route_Node(insertion_node.node_type, insertion_node.id, insertion_node_start, insertion_node_end)
        new_route = prev_nodes + [insertion_node] + next_nodes

        if next_nodes[0].node_type == NodeType.TASK:
            
            if insertion_node_end + travel_insertion_to_next + next_task_duration < next_task_start_feasability:
                #print(insertion_node_end + travel_insertion_to_next + next_task_duration, next_task_start_feasability)
                #insertion_node.start_time = insertion_node_start
                #insertion_node.end_time = insertion_node_end

                return feasability,new_node, new_route, True
        
        elif next_nodes[0].node_type == NodeType.TECH:
            if insertion_node_end + travel_insertion_to_next < next_task_start_feasability:
                
                #insertion_node.start_time = insertion_node_start
                #insertion_node.end_time = insertion_node_end

                return feasability,new_node, new_route, True
        
        else: # ! next node nothing
            #insertion_node.start_time = insertion_node_start
            #insertion_node.end_time = insertion_node_end


            return feasability,new_node, new_route, True
        
        return feasability,None, [], False


    def leftSide_twCheck(self, node, task):
        if task.end_tw + TASK_OVERTIME == node.end_time: # since task is at over time then we can't change anything on left side, right side left only
            return True
        return False

    
    def task_insertion(self, prev_nodes, insertion_task, next_nodes, tech, tasks, distances, weather):
        feasability_reason = ""
        feasable = False
        new_starts = []
        feasability_reason, new_node, new_route, feasable = self.one_nodeInsertion(prev_nodes, insertion_task, next_nodes, tech, tasks, distances, weather) #!
        new_starts.append(new_node)
        #singleInsert +=1

        if not feasable: #! rebuilding whole route
            #singleInsert -=1
            new_starts.clear()
            # ! should consider if both sides need rebuilding or can only left side or right side
            
            insertion_index = len(prev_nodes)
            # ! if ends at end_tw + overtime then on right side can't change anything 
            #print("insertion_index ", insertion_index)
            #print("prev_nodes[insertion_index-1] ", prev_nodes[insertion_index-1])
            
            is_technician = False
            if prev_nodes[-1].node_type == NodeType.TECH:
                prev_node = tech
                is_technician = True
            else:
                #print(tasks[prev_nodes[-1].id])
                prev_node = tasks[prev_nodes[-1].id]

            not_right_side = False
            
            if not is_technician: 
                if self.leftSide_twCheck(prev_nodes[insertion_index-1], prev_node): #! unless it is technician
                    #rightOnly += 1
                    feasability_reason, new_node, new_route, feasable = self.insertion_feasability(prev_nodes[-1], insertion_task, next_nodes[0], tech, tasks, distances, weather) #!
                    #new_node, new_route, feasable = self.insertion_feasability(prev_nodes, insertion_task, next_nodes, tech, tasks, distances) #!
                    
                    new_starts.append(new_node)

                    #route = [prev_nodes[-1]] + [insertion_task] + next_nodes
                    route = [n.copy_node() for n in ([prev_nodes[-1]] + [insertion_task] + next_nodes)]
                    route[len(prev_nodes)] = new_node
                    for i in range(len(route)-2):
                        if i+2 > len(route)-1:
                            break
                        #print("a2: ", i, len(route)-1)

                        if i+1 > len(route)-1:
                            break
                        #print("a3: ", i, len(route)-2)

                        if route[i+1].node_type == NodeType.TECH:
                            continue
                        #print("a4: ", i, len(route)-2)
                        #print(route)
                        feasability_reason, new_node, new_route, feasable = self.insertion_feasability([route[i]], route[i+1], [route[i+2]], tech, tasks, distances, weather) #!
                        #new_node, new_route, feasable = self.insertion_feasability(route[:i], route[i+1], route[i+2:], tech, tasks, distances) #!
                        
                        if not feasable:
                            #rightOnly -= 1
                            break
                        #print(route)    
                        route[i+1] = new_node
                        new_route = route
                        new_starts.append(new_node)
                        #print(route)
                        #route = new_route
                    #new_route = 
                else:
                    not_right_side =True
                    
                
            
            if not_right_side or is_technician:
                #rightOnly -= 1
                #fullRestart += 1
                new_starts.clear()
                #route = prev_nodes + [insertion_task] + next_nodes
                route = [n.copy_node() for n in (prev_nodes + [insertion_task] + next_nodes)]
                #print(route)
                for i in range(len(route)-2): # * 0 1 2 3 4
                    #print("a1: ", i, len(route)-2)

                    if i+2 > len(route)-1:
                        break
                    #print("a2: ", i, len(route)-1)

                    if i+1 > len(route)-1:
                        break
                    #print("a3: ", i, len(route)-2)

                    if route[i+1].node_type == NodeType.TECH:
                        continue
                    #print("a4: ", i, len(route)-2)
                    printing = False
                    if printing:
                        for node in route:
                            if node.node_type == NodeType.TASK:
                                print("TAAASK: ", node.node_type, node.id, node.start_time, node.end_time)
                            else:
                                print(node.node_type, node.id, node.start_time, node.end_time)
                            
                        print([route[i]], route[i+1], [route[i+2]])

                    feasability_reason, new_node, new_route, feasable = self.insertion_feasability([route[i]], route[i+1], [route[i+2]], tech, tasks, distances, weather) #!
                    #new_node, new_route, feasable = self.insertion_feasability(route[:i], route[i+1], route[i+2:], tech, tasks, distances) #!

                    #print(feasable, route[i+1])
                    if  not feasable:
                        #fullRestart -= 1
                        break
                    printing = False
                    if printing:
                        for node in route:
                            if node.node_type == NodeType.TASK:
                                print("TAAASK: ", node.node_type, node.id, node.start_time, node.end_time)
                            else:
                                print(node.node_type, node.id, node.start_time, node.end_time)
                        print()
                    route[i+1] = new_node
                    new_route = route
                    #print(route)
                    new_starts.append(new_node)
                #print(new_starts)   

        
        if not feasable:
            
            return feasability_reason, [], False    
        #print("waaaaaaaaaaaaaaaaa")
        
        updated_route = deepcopy(new_route)
        for node in new_starts:
            for i in range(len(updated_route)):
                if updated_route[i].id == node.id:
                    updated_route[i].start_time = node.start_time
                    updated_route[i].end_time = node.end_time
                    
        return "", updated_route, feasable
        #return new_starts, new_route, feasable


    def tech_goRestock(self, firstResourceFailurePoint, route, tech, tasks, distances, resources_needed, restocking_nodes,data,weather):
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
        feasability = ""
        current_tech_location = Distance_Node(NodeType.TECH, tech.master_id)
        # 1. can we even restock
        cost = 0.0
        is_restocked = False
        restocking_route = route
        #print(resources_needed.values())
        
        totalNeededResources = 0
        for value in resources_needed.values():
            totalNeededResources += value[0]

        #print("totalNeededResources",totalNeededResources)


        techvanSize = sum(tech.resources.values())
        #print(techvanSize)
        
        currentTech_availableVanSize = VANSIZE - techvanSize # wont work because tech vansize is a list
        #print(currentTech_availableVanSize)

        for i in range(firstResourceFailurePoint-1):
            indx = i + 1
            if route[indx].node_type not in (NodeType.TASK, NodeType.TECH):
                continue
            
            if route[indx].node_type is NodeType.TASK:
                try:
                    techvanSize -= sum(tasks[route[indx].id].resources)
                except KeyError as e:
                    print(route[i])

                    raise

                currentTech_availableVanSize = VANSIZE - techvanSize
            
            if DEPOT_TEST:
                for depot in restocking_nodes[1].values():
                    depot_node = Route_Node(NodeType.DEPOT, depot.id, start_time=None, end_time=None)

                    new_route = route # ! should copy
                    
                    #new_node, new_route, feasable = self.insertion_feasability(route[:indx], depot_node, route[indx:], tech, tasks, distances)
                    feasability, new_node, new_route, feasable = self.one_nodeInsertion(route[:indx], depot_node, route[indx:], tech, tasks, distances, weather)
                    new_starts = []
                    new_starts.append(new_node)
                
                    if not feasable:
                        continue

                    updated_route = deepcopy(new_route)
                    for node in new_starts:
                        for i in range(len(updated_route)):
                            if updated_route[i].id == node.id and updated_route[i].node_type == node.node_type :
                                updated_route[i].start_time = node.start_time
                                updated_route[i].end_time = node.end_time

                    cost = self.calculateRouteCost(updated_route, distances, tasks,data, weather, tech)
                    candidates.append((cost, updated_route))
                
            if currentTech_availableVanSize < totalNeededResources:
                continue
            ## if tech does not have necessary resources at this point we consider to go to depo/shop at any point in previous tasks.
            
            if SHOP_TEST:
                for shop in restocking_nodes[0].values():
                    #print(shop)
                    #if shop.node_type is not NodeType.SHOP:
                    #    continue
                    shop_node = Route_Node(NodeType.SHOP, shop.id, start_time=None, end_time=None)
                    #if not self.timeWindow_feasabilityTECH([route[i], shop_node, route[i+1]], tech, distances, tasks):
                    #    continue

                    new_route = route # ! should copy
                    
                    ## ! try to insert, maybe no need to rebuild, if can't insert then try to rebuild the route
                    #pre_end + travel + insertion_duration + travel + next_start
                    #new_node, new_route, feasable = self.insertion_feasability(route[:indx], shop_node, route[indx:], tech, tasks, distances)
                    feasability, new_node, new_route, feasable = self.one_nodeInsertion(route[:indx], shop_node, route[indx:], tech, tasks, distances, weather)
                    new_starts = []
                    new_starts.append(new_node)
                    ## ! try to rebuild from insertion outwards?
                    #new_route.insert(i + 1, shop_node)
                    
                    #new_route, feasable = self.full_feasability(new_route)
                    if not feasable:
                        continue

                    updated_route = deepcopy(new_route)
                    for node in new_starts:
                        for i in range(len(updated_route)):
                            if updated_route[i].id == node.id and updated_route[i].node_type == node.node_type :
                                updated_route[i].start_time = node.start_time
                                updated_route[i].end_time = node.end_time

                    cost = self.calculateRouteCost(updated_route, distances, tasks,data,weather,tech)
                    candidates.append((cost, updated_route))
        
        # ! comparte candidates and choose best
        
        if len(candidates):
            #print("restock", end=" ")
            
            
            candidates.sort(key=lambda x: x[0]) # negative on left and positive on right side

            chosen = candidates[0]
            
            cost, new_route = chosen
            
            restocking_route = new_route
            printing = False
            #print(cost, end=" ")
            
            if printing:
                print()
                for node in new_route:
                    
                    if node.node_type == NodeType.TASK:
                        print("TAAASK: ", node.node_type, node.id, node.start_time, node.end_time)
                    else:
                        print(node.node_type, node.id, node.start_time, node.end_time)

            is_restocked = True
            return feasability, restocking_route, cost, is_restocked
        else:
            return feasability, [], 0, False
        

        # for route
        return route, cost, is_restocked
        

    ### ! if can insert task without affecting the surrounding tasks at current time then we just insert and move on
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
    #current_techLocation = Distance_Node(NodeType.TECH, tech.master_id)
        
    #currentTime = tech.start_tw 
    #shiftEnd = tech.end_tw
    
    #overTime = 0
    #taskOverTime = 0
    def routeCost_and_feasability(self, new_route, tech, distances, tasks, data, restocking_nodes,weather): # creates new route considering everything that is hard feasability # weather is when insertion is possible 
        cost = 0.0
        

        ### need to collect all resources and check when each possible time to go to shop
        total_resourcesUsed = {}
        total_resourcesToRestock = {}
        feasability = ""
        needed_toRestock = False
        currentNode = 0
        firstResourceFailurePoint = -1

        ### ! recomputes too often
        for node in new_route:
            if node.node_type == NodeType.TASK:
                for resource_id in tasks[node.id].resources:
                    if resource_id not in total_resourcesUsed:
                        total_resourcesUsed[resource_id] = [0, 0.0] 

                    total_resourcesUsed[resource_id][0] += 1 # saves resouce count needed
                    total_resourcesUsed[resource_id][1] += data.resource_cost[resource_id] # saves cost
                

                    resource_data = total_resourcesUsed.get(resource_id)
                    resource_used = resource_data[0]
                    tech_resource_store = 0

                    if resource_id not in tech.resources.keys():
                        tech_resource_store = 0
                    else:
                        tech_resource_store = tech.resources.get(resource_id)
                    
                    #print(tech_resource_store, resource_used, tech_resource_store < resource_used)
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

        """for key, value in total_resourcesUsed.items():
            if resource_id not in tech.resources.keys():
                tech_res = 0
            else:
                tech_res = tech.resources.get(resource_id)
            
            if resource_id not in total_resourcesToRestock.keys():
                restoc = 0
            else:
                restoc = total_resourcesToRestock[resource_id][0]

        
            print(total_resourcesUsed[resource_id][0], tech_res,restoc)
        """    
        
        if needed_toRestock:
            restocking_route = [] ### ! cannot do this because shops influece currentNode variable or can do it? # can
            for node in new_route:
                if node.node_type in (NodeType.TASK, NodeType.TECH):
                    restocking_route.append(node) #* create route without shops or depots
            

            # % we insert both new restocking node and task at current insert location or not
            #print(firstResourceFailurePoint)
            feasability, restocking_route, resource_costs, is_restocked = self.tech_goRestock(firstResourceFailurePoint, restocking_route, tech, tasks, distances, total_resourcesToRestock, restocking_nodes,data,weather)
            
         
            #print("total_resourcesUsed: ", total_resourcesUsed)
            #print("total_resourcesToRestock: ", total_resourcesToRestock)
            #print("needed_toRestock: ", needed_toRestock)
            #print("firstResourceFailurePoint: ", firstResourceFailurePoint)
            if is_restocked:

                
                printing = False
                
                if printing:
                    print()
                    print("got a positive")
                    print(cost, end=" ")
                    print()
                    for node in new_route:
                        if node.node_type == NodeType.TASK:
                            print("TAAAAASK: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.SHOP:
                            print("SHOPPP: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.DEPOT:
                            print("DEPOOOOOT: ", node.node_type, node.id, node.start_time, node.end_time)
                        else:
                            print("TE: ", node.node_type, node.id, node.start_time, node.end_time)
                    print()
                return feasability, restocking_route, True

            else:
                return feasability, new_route, False #not feasable to go to shop and retain all tasks
            
            ## * cost should be gotten from resources_needed ignoring the resources that needed restock ## * total_resources - resources_restocked
            
            # ! need to save technician van somewhere, every task or at end of task?
            for resource_id, values in total_resourcesToRestock.items():
                new_cost = total_resourcesUsed[resource_id][1] / total_resourcesUsed[resource_id][0] * (total_resourcesUsed[resource_id][0] - values[0]) 
                total_resourcesUsed[resource_id][0] -= values[0]
                total_resourcesUsed[resource_id][1] -= new_cost
            cost += resource_costs
            
            for cost_resource in total_resourcesUsed.values():
                cost += cost_resource[1]
        
            return new_route, True
        
        else:
            if tech.master_id == 34:
                #print(total_resourcesToRestock)
                pass
            return feasability, new_route, True
            
            
    def greedy(self, solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes, weather):
        #print(solution)
        #print()
        #print(technicians)
        new_solution = solution.copy()
        
        indx3 = 0
        unfeasable_tasks = []
        removable_tasks = []
        iters = len(unassigned_tasks)
        once = 0

        while unassigned_tasks and indx3 < iters+5: ### set itteration count for stopping inf loop, ### no infinite loop because of pop
            if indx3 % 5 == 0:
                print(indx3)
            candidates = []
            for task in unassigned_tasks:
                indx = 0
                for tech_id, tech in technicians.items():
                    #print(1)
                    #if indx % 5 == 0:
                    #    print(indx)
                    if not self.assign_feasability(tasks[task.id], tech, distances): ### Checks if skills and time_window is within limits
                        feasability_reason = "lack skills"
                        continue

                    
                    old_cost = new_solution.monetaryCost[tech.master_id]
                    new_task_insertion = Route_Node(NodeType.TASK, task.id, start_time=None, end_time=None) #task.start_tw
                    #route = deepcopy(new_solution.routes[tech.master_id])
                    route = []
                    for node in new_solution.routes[tech.master_id]:
                        if node.node_type in [NodeType.TASK, NodeType.TECH]:
                            route.append(node)       
                    #route = new_solution.routes[tech.master_id]
                    indx2=0
                    
                    #print(route)
                    for position in range(len(route) - 2): 
                        #print("a")
                        #print(indx2)
                        #print(len(new_solution.routes), end=" ")
                        position += 1
                        ### * does not consider that task insertion can happen so that technciian starts task and all future tasks get ignored because current one takes too long
                        ### * does not consider if there is any available time (min duration of task)
                        ### * does not consider tech start home and end home
                        if route[position].node_type in [NodeType.SHOP, NodeType.DEPOT]: #! wat      task depo insertion task
                            continue
                        #print()
                        if route[position+1].node_type in [NodeType.SHOP, NodeType.DEPOT]: #! wat        task insertion depo task
                            continue
                        #if route[position].node_type != NodeType.TECH and route[position+1].node_type != NodeType.TECH:
                        """
                        if indx > 15:
                            if route[position].node_type == NodeType.TECH or route[position+1].node_type == NodeType.TECH: 
                                tech_count +=1
                            if route[position].node_type == NodeType.TASK or route[position+1].node_type == NodeType.TASK:
                                task_count +=1
                            
                            print(tech_count, task_count)
                            print(self.timeWindow_feasabilityTECH([route[position], new_task_insertion, route[position+1]], tech, distances, tasks))
                        """
                        #print("a2")
                        #print()
                        #print(position)
                        #print(route[:position])
                        #return False
                        if not self.timeWindow_feasability([route[position], new_task_insertion, route[position+1]], tech, distances, tasks):
                            feasability_reason = "cannot fit in timewindow"
                            continue
                        
                        #else:
                        #    if not self.timeWindow_feasabilityTECH([route[position], new_task_insertion, route[position+1]], distances, tasks):
                        #        continue

                        feasability_reason, new_route, feasable = self.task_insertion(route[:position], new_task_insertion, route[position:], tech, tasks, distances, weather)

                        if feasable: # ! restocking
                            feasability_reason, new_route, feasable = self.routeCost_and_feasability(new_route, tech, distances, tasks, data, restocking_nodes,weather) 
                            if not feasable:
                                continue
                        
                        if feasable:
                            new_cost = 0.0 
                            #for new_node in new_nodes:
                            #    new_cost += self.calculateRouteCost(new_node.start_time,new_node.end_time,new_node.id,new_route, distances, tasks) 
                            
                            new_cost = self.calculateRouteCost(new_route, distances, tasks, data, weather, tech)
                            difference = new_cost - old_cost 
                            #candidates.append((difference, new_nodes, new_route, tech.master_id, position, task.id))
                            candidates.append((difference, new_route, tech.master_id, position, task.id))
                            
                            indx2 +=1
                    indx += 1
                        
                print(feasability_reason)
                if not candidates:
                    #new_solution.task_feasability[task.id] = feasability_reason
                    is_inList = False
                    for utask in unfeasable_tasks:
                        if utask.id == task.id:
                            is_inList = True
                    if not is_inList:
                        unfeasable_tasks.append(task)
                        removable_tasks.append(task)
            indx3 +=1
            #print(indx3)
            if indx % 5 == 0:
                print(indx, end=" ")
            if candidates:
                once += 1
                
                print(indx, end=" ")
                if indx % 5 == 0:
                    print()
                for task in removable_tasks:
                    unassigned_tasks = [t for t in unassigned_tasks if t.id != task.id]

                candidates.sort(key=lambda x: x[0]) # negative on left and positive on right side

                chosen = candidates[0]
                #cost, new_nodes, new_route, tech_id, pos, task_id = chosen
                cost, new_route, tech_id, pos, task_id = chosen
                """
                for i in range(len(new_route)-1):
                    for new_node in new_nodes:
                        if new_route[i].id == new_node.id and new_route[i].node_type == new_node.node_type:
                            #print(new_route[i])
                            new_route[i] = new_node
                            #print(new_route[i])
                            #print("wow")
                """

                new_solution.routes[tech_id] = new_route
                new_solution.changedRoute[tech_id] = True
                printing = True
                print()
                
                print(cost, end=" ")
                print()
                if printing:
                    for node in new_route:
                        if node.node_type == NodeType.TASK:
                            print("TAAAAASK: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.SHOP:
                            print("SHOPPP: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.DEPOT:
                            print("DEPOOOOOT: ", node.node_type, node.id, node.start_time, node.end_time)
                        else:
                            print("TE: ", node.node_type, node.id, node.start_time, node.end_time)
                print()
                print()
                #if indx > 30:
                #    time.sleep(3)
                unassigned_tasks = [t for t in unassigned_tasks if t.id != task_id]

        #print("waaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaat: ", len(unfeasable_tasks))
        #print(unfeasable_tasks)
        #print()
        #print()
        return new_solution, unfeasable_tasks
    

    def regret(self, solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes, weather):
        #print(solution)
        #print()
        #print(technicians)
        new_solution = solution.copy()
        indx = 0
        indx3 = 0
        unfeasable_tasks = []
        removable_tasks = []
        iters = len(unassigned_tasks)
        once = 0

        while unassigned_tasks and indx3 < iters+5: ### set itteration count for stopping inf loop, ### no infinite loop because of pop
            candidates = []
            indx = 0
            if indx3 % 5 == 0:
                print(indx3)
            for task in unassigned_tasks:
                feasability_reason = ""
                #if indx % 5 == 0:
                    #print(indx)
                insertion_nodes = []
                for tech_id, tech in technicians.items():
                    
                    #print(route)
                    #print(1)
                    if not self.assign_feasability(tasks[task.id], tech, distances): ### Checks if skills and time_window is within limits
                        feasability_reason = "cannot fit in timewindow"
                        continue

                    
                    old_cost = new_solution.monetaryCost[tech.master_id]
                    new_task_insertion = Route_Node(NodeType.TASK, task.id, start_time=None, end_time=None) #task.start_tw
                    #route = deepcopy(new_solution.routes[tech.master_id])
                    route = []
                    for node in new_solution.routes[tech.master_id]:
                        if node.node_type in [NodeType.TASK, NodeType.TECH]:
                            route.append(node)       
                    #route = new_solution.routes[tech.master_id]
                    indx2=0

                    #print(route)

                    for position in range(len(route) - 2):   
                        position += 1 
                        if route[position].node_type in [NodeType.SHOP, NodeType.DEPOT]: #! wat      task depo insertion task
                            continue
                        if route[position+1].node_type in [NodeType.SHOP, NodeType.DEPOT]: #! wat        task insertion depo task
                            continue
                        if not self.timeWindow_feasability([route[position], new_task_insertion, route[position+1]], tech, distances, tasks):
                            continue
                        #print()
                        #print(position)
                        #print(route[:position])
                        feasability, new_route, feasable = self.task_insertion(route[:position], new_task_insertion, route[position:], tech, tasks, distances, weather)

                        if feasable: # ! restocking
                            feasability_reason, new_route, feasable = self.routeCost_and_feasability(new_route, tech, distances, tasks, data, restocking_nodes,weather) 
                            if not feasable:
                                continue
                        
                        if feasable:

                            cost = self.calculateRouteCost(new_route, distances, tasks, data, weather,tech)
                            insertion_nodes.append((cost, new_route, tech.master_id, position, task.id))
                            indx2 +=1
                print(feasability_reason)
                if insertion_nodes:
                    insertion_nodes.sort(key=lambda x: x[0])
                    best_cost = insertion_nodes[0][0]
                    if len(insertion_nodes) > 1:
                        second_best_cost = insertion_nodes[1][0]
                    else:
                        second_best_cost = best_cost 

                    regret_cost = second_best_cost - best_cost
                    cost, new_route, tech_id, position, task_id = insertion_nodes[0]
                    candidates.append((regret_cost, new_route, tech_id, position, task_id))
                    #print(candidates)

                if not candidates:
                    is_inList = False
                    for utask in unfeasable_tasks:
                        if utask.id == task.id:
                            is_inList = True
                    if not is_inList:
                        unfeasable_tasks.append(task)
                        removable_tasks.append(task)
    
            
                indx += 1
            indx3 +=1
            #print(indx3)
                
            if candidates:
                once += 1
                
                for task in removable_tasks:
                    unassigned_tasks = [t for t in unassigned_tasks if t.id != task.id]

                candidates.sort(key=lambda x: x[0]) # negative on left and positive on right side

                chosen = candidates[0]
                cost, new_route, tech_id, pos, task_id = chosen


                new_solution.routes[tech_id] = new_route
                new_solution.changedRoute[tech_id] = True
                printing = True
                print()
                
                print(cost, end=" ")
                print()
                if printing:
                    for node in new_route:
                        if node.node_type == NodeType.TASK:
                            print("TAAAAASK: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.SHOP:
                            print("SHOPPP: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.DEPOT:
                            print("DEPOOOOOT: ", node.node_type, node.id, node.start_time, node.end_time)
                        else:
                            print("TE: ", node.node_type, node.id, node.start_time, node.end_time)
                print()
                print()
                #if indx > 30:
                #    time.sleep(3)
                unassigned_tasks = [t for t in unassigned_tasks if t.id != task_id]


        return new_solution, unfeasable_tasks


    

    def random(self, solution, unassigned_tasks, technicians, tasks, distances, data, restocking_nodes, weather):
        new_solution = solution.copy()
        
        unfeasable_tasks = []
        removable_tasks = []
        tech_list = []

  
        indx = 0
        indx3 = 0
        iters = len(unassigned_tasks)
        once = 0

        for key, tech in technicians.items():
            tech_list.append(tech)
        while unassigned_tasks:
            candidates = []

            print("LENGHTHTH: ",len(unassigned_tasks))
            task = random.choice(unassigned_tasks)

            tech_list_index = list(range(len(tech_list)))
            for i in range(len(technicians)):
                feasable = False
                index = random.choice(tech_list_index)
                tech = tech_list[index]
                tech_list_index.remove(index)
            
                if not self.assign_feasability(tasks[task.id], tech, distances): ### Checks if skills and time_window is within limits
                    continue
            
                old_cost = new_solution.monetaryCost[tech.master_id]
                new_task_insertion = Route_Node(NodeType.TASK, task.id, start_time=None, end_time=None) #task.start_tw
                
                route = []
                for node in new_solution.routes[tech.master_id]:
                    if node.node_type in [NodeType.TASK, NodeType.TECH]:
                        route.append(node)    

                for position in range(len(route) - 2):    
                    feasable = False
                    position += 1
            
                    if route[position].node_type in [NodeType.SHOP, NodeType.DEPOT]: #! wat      task depo insertion task
                        continue
                    if route[position+1].node_type in [NodeType.SHOP, NodeType.DEPOT]: #! wat        task insertion depo task
                        continue
                    if not self.timeWindow_feasability([route[position], new_task_insertion, route[position+1]], tech, distances, tasks):
                        continue

                    feasability, new_route, feasable = self.task_insertion(route[:position], new_task_insertion, route[position:], tech, tasks, distances, weather)

                    if feasable: # ! restocking
                        feasability_reason, new_route, feasable = self.routeCost_and_feasability(new_route, tech, distances, tasks, data, restocking_nodes,weather) 
                        if not feasable:
                            continue
                    
                    if feasable:
                        new_cost = 0.0 
                        #for new_node in new_nodes:
                        #    new_cost += self.calculateRouteCost(new_node.start_time,new_node.end_time,new_node.id,new_route, distances, tasks) 
                        
                        new_cost = self.calculateRouteCost(new_route, distances, tasks, data, weather,tech)
                        difference = new_cost - old_cost 
                        #candidates.append((difference, new_nodes, new_route, tech.master_id, position, task.id))
                        candidates.append((difference, new_route, tech.master_id, position, task.id))
                            
                        #indx2 +=1
                        break
                if feasable:
                    break
            
            if not candidates:
                is_inList = False
                for utask in unfeasable_tasks:
                    if utask.id == task.id:
                        is_inList = True
                if not is_inList:
                    #print("aaaaaaaaaaaaaaaaaaaaaaaa")
                    unfeasable_tasks.append(task)
                    
                    unassigned_tasks.remove(task)
            
            if candidates:
                once += 1
                indx += 1
                print(indx, end=" ")
                if indx % 5 == 0:
                    print()

                candidates.sort(key=lambda x: x[0])
                chosen = candidates[0]
                cost, new_route, tech_id, pos, task_id = chosen

                new_solution.routes[tech_id] = new_route
                new_solution.changedRoute[tech_id] = True
                printing = True

                if printing:
                    for node in new_route:
                        if node.node_type == NodeType.TASK:
                            print("TAAAAASK: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.SHOP:
                            print("SHOPPP: ", node.node_type, node.id, node.start_time, node.end_time)
                        elif node.node_type == NodeType.DEPOT:
                            print("DEPOOOOOT: ", node.node_type, node.id, node.start_time, node.end_time)
                        else:
                            print("TE: ", node.node_type, node.id, node.start_time, node.end_time)
                print()
                print()
                #if indx > 30:
                #    time.sleep(3)
                
                unassigned_tasks.remove(task)

                

        #print(unfeasable_tasks)
        return new_solution, unfeasable_tasks
    
    def __str__(self):
        pass


class ALNS_ALgorithm: 
    def __init__(self, run_time = 60.0, simulatedAnnealing_temperature = 200.0, simulatedAnnealing_cooling = 0.995):
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
        self.current_unassigned_tasks = []

        self.distances = Distances()
        self.shops = {}
        self.depots = {}
        self.data = Resource_Data()
        self.weather = Weather()
        self.task_relatedness: Dict[Tuple[int,int], float] = {}
        self.related_list = []

        self.start_time = time
        self.end_time = time
        self.iteration = ""
        

    def normalize_values(self, dictionary):
        values = list(dictionary.values())
        min_val = min(values)
        max_val = max(values)
        
        # Avoid division by zero if all values are equal
        if min_val == max_val:
            return {k: 1.0 for k in dictionary}
        
        return {key: (value - min_val) / (max_val - min_val) for key, value in dictionary.items()}

    def relatedness(self):
        #
        # read existing data
        relateddnz = urls.relatedness_cache
        file_exists = os.path.exists(relateddnz)
        existing_keys = set()

        if file_exists:
            with open(relateddnz, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile, delimiter=';')
                for row in reader:
                    
                    a = int(row["a_id"])
                    b = int(row["b_id"])
                    relatedness = float(row["related"])

                    self.task_relatedness[(a,b)] = relatedness
                    if a not in self.related_list:
                        self.related_list.append(a)
                    
                    if b not in self.related_list:
                        self.related_list.append(b)
                   
            infile.close()
        #
        relatedness_duration: Dict[Tuple[int,int], float] = {}
        relatedness_resource: Dict[Tuple[int,int], float] = {}
        relatedness_skill: Dict[Tuple[int,int], float] = {}
        relatedness_timeWindow: Dict[Tuple[int,int], float] = {}
        

        for id_1, task_1 in self.tasks.items():
            #print(task_1)
            if task_1 in self.related_list:
                continue
            for id_2, task_2 in self.tasks.items():
                #print("taks2: ", task_2)
                if task_1.id == task_2.id:
                    continue
                if not relatedness_duration: 
                    if (task_2.id,task_1.id) in relatedness_duration:
                        continue
                #print(relatedness_duration)

                relatedness_duration[(task_1.id,task_2.id)] = 1
                relatedness_resource[(task_1.id,task_2.id)] = 1
                relatedness_skill[(task_1.id,task_2.id)] = 1
                relatedness_timeWindow[(task_1.id,task_2.id)] = 1

                

                
                relatedness_duration[(task_1.id,task_2.id)] = abs(task_1.duration-task_2.duration)
                
                for resource_1 in task_1.resources:
                    if resource_1 in task_2.resources:
                        relatedness_resource[(task_1.id,task_2.id)] +=1
   
                for skill_1 in task_1.skills:
                    if skill_1 in task_2.skills:
                        relatedness_skill[(task_1.id,task_2.id)] += 1

                #relatedness_timeWindow = #??
                relatedness_timeWindow[(task_1.id,task_2.id)] = min(task_1.end_tw, task_2.end_tw) - max(task_1.start_tw, task_2.start_tw)



            self.related_list.append(task_1.id)
            
        # normalize all relatedness and create task_relatendess without distances
        relatedness_duration = self.normalize_values(relatedness_duration)
        relatedness_resource = self.normalize_values(relatedness_resource)
        relatedness_skill = self.normalize_values(relatedness_skill)
        relatedness_timeWindow = self.normalize_values(relatedness_timeWindow)

        ## count into one relatedness and then top 20% get their relatedness added with distances
        for key in relatedness_duration.keys():
            duration = relatedness_duration[key]
            resource = relatedness_resource[key]
            skill = relatedness_skill[key]
            timeWindow = relatedness_timeWindow[key]

            self.task_relatedness[key] = duration + resource + skill + timeWindow 

        #print(self.task_relatedness)
        self.task_relatedness = dict(sorted(self.task_relatedness.items(), key=lambda x: x[1], reverse=True))
        #print(self.task_relatedness)
        """top_count = max(1, int(len(self.tasks) * 0.2))
        sorted_top_pairs = sorted(self.task_relatedness.items(), key=lambda x: x[1], reverse=True)[:top_count]

        for i in len(sorted_top_pairs):
            a = Distance_Node(NodeType.TASK, sorted_top_pairs[0])
            b = Distance_Node(NodeType.TASK, sorted_top_pairs[0])

            distance = self.distances.get_distance(a,b)"""

        #! cache data
        relatedness_file = urls.relatedness_cache
        file_exists = os.path.exists(relatedness_file)
        existing_keys = set()

        if file_exists:
            with open(relatedness_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile, delimiter=';')
                for row in reader:
                    key = (
                        int(row["a_id"]),
                        int(row["b_id"])
                    )
                    existing_keys.add(key)
                   
            infile.close()

        with open(relatedness_file, 'a', newline='', encoding='utf-8') as outfile: 
            fieldnames = ["a_id","b_id","related"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
            
            if not file_exists:
                writer.writeheader()

            for keys, values in self.task_relatedness.items():
                key = (keys[0],keys[1])
                
                if key in existing_keys:
                    continue

                row = {"a_id":keys[0],"b_id":keys[1],
                       "related":values}

                writer.writerow(row)
            
        outfile.close()

        
    def readData(self): # ***
        path = urls.taskFilePath
        with open(path) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                task_id = int(row["id"])
                if (datetime.datetime.fromisoformat(str(row["start_tw"]))) != (datetime.datetime.fromisoformat(str(row["end_tw"]))):
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
                    if (datetime.datetime.fromisoformat(str(row["start_tw"]))) != (datetime.datetime.fromisoformat(str(row["end_tw"]))):
                        self.technicians[master_id].start_tw.append(start_tw)
                        self.technicians[master_id].end_tw.append(end_tw)
                    
                else:
                    if (datetime.datetime.fromisoformat(str(row["start_tw"]))) != (datetime.datetime.fromisoformat(str(row["end_tw"]))):
                     self.technicians[master_id] = Technician(row)

        f.close()

        
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
        

        
    def construct(self): # ***

        self.distances.add_coords(NodeType.TASK, self.tasks)
        self.distances.add_coords(NodeType.TECH, self.technicians)
        self.distances.add_coords(NodeType.DEPOT, self.depots)
        self.distances.add_coords(NodeType.SHOP, self.shops)

        self.distances.add_distances_from_file()
        self.relatedness()
        #?self.distances = self.distances.add_coords(NodeType.DEPOT, self.tasks)
        #?self.distances = self.distances.add_coords(NodeType.SHOP, self.tasks)


        self.new_solution = Solution(self.technicians, self.tasks)


        """for master_id, route in self.new_solution.routes.items():
            for i in range(len(self.technicians[master_id].start_tw)):
                route.append(Route_Node(NodeType.TECH, master_id, start_time=self.technicians[master_id].start_tw[i], end_time=self.technicians[master_id].start_tw[i]))
                route.append(Route_Node(NodeType.TECH, master_id, start_time=self.technicians[master_id].end_tw[i], end_time=self.technicians[master_id].end_tw[i])) 
        """
        for master_id, route in self.new_solution.routes.items():
            tech_nodes = []

            # Collect TECH start/end nodes for this technician
            for i in range(len(self.technicians[master_id].start_tw)):
                tech_nodes.append(
                    Route_Node(
                        NodeType.TECH,
                        master_id,
                        start_time=self.technicians[master_id].start_tw[i],
                        end_time=self.technicians[master_id].start_tw[i]
                    )
                )
                tech_nodes.append(
                    Route_Node(
                        NodeType.TECH,
                        master_id,
                        start_time=self.technicians[master_id].end_tw[i],
                        end_time=self.technicians[master_id].end_tw[i]
                    )
                )

            # Sort the TECH nodes by start_time
            tech_nodes.sort(key=lambda node: node.start_time)

            # Rebuild the route with sorted TECH nodes but keep other nodes in place

            route.extend(tech_nodes)
        
        
        task_ids = list(self.tasks.keys())
        random.shuffle(task_ids)
        
        # * fill routes with tech home and home for every time window
        
        for id in task_ids:
            self.unassigned_tasks.append(Route_Node(NodeType.TASK, id, start_time=None, end_time=None))
        #print(self.new_solution)
        ###! Greedy, have to finish operators first
        self.new_solution, self.unassigned_tasks = self.operators.repair(self.new_solution, self.unassigned_tasks, self.technicians, self.tasks, self.distances, self.data, [self.shops, self.depots],self.weather)
        print("right after repair")
        #print(self.new_solution)
        self.current_unassigned_tasks = deepcopy(self.unassigned_tasks)

        self.new_solution.updateCosts_Income(self.distances,self.tasks, self.unassigned_tasks, self.weather)
        self.best_solution = deepcopy(self.new_solution)
        self.current_solution = deepcopy(self.new_solution)


    def selectOperators(self): # ***
        self.operators.roulette()


    def generateNewSolution(self): # ***
        for i in range(len(self.unassigned_tasks)):
            self.unassigned_tasks[i].start_time = None
            self.unassigned_tasks[i].end_time = None
        print(len(self.unassigned_tasks))
        print(len(self.tasks))
        print(len(self.technicians))

        #if 
        self.new_solution, self.unassigned_tasks = self.operators.destroy(self.current_solution, self.unassigned_tasks, self.tasks, self.task_relatedness)
        print("repair")
        self.new_solution, self.unassigned_tasks = self.operators.repair(self.new_solution, self.unassigned_tasks, self.technicians, self.tasks, self.distances, self.data, [self.shops, self.depots],self.weather)
        

    def acceptSimulatedAnnealingFunction(self): # ***
        

        delta = self.new_solution.weight - self.current_solution.weight
        if delta <= 0:
            return True
    
        prob = min(1.0, math.exp(-delta / self.simulatedAnnealing_temperature))
        
        return random.random() < prob


    def updateWeights(self): # ***
        self.operators.renew_weights(self.score)

    def saveData(self):
        weather_file = urls.data_collection
        file_exists = os.path.exists(weather_file)

        with open(weather_file, 'a', newline='', encoding='utf-8') as outfile: 
            fieldnames = ["iteration","totalMonetaryCost","totalPathCost","totalTimeCost",
                            "totalWeatherExtraTime","totalWeatherSafetyRiskKm","totalWeatherCost",
                            "totalShopCost","totalDepotCost","totalResourceCost",
                            "totalIncome","forgottenTaskCost","weight","time","destroy","repair"]
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
            
            if not file_exists:
                writer.writeheader()
            time = self.end_time-self.start_time
            row = {
                    "iteration": self.iteration,
                    "totalMonetaryCost": round(self.best_solution.totalMonetaryCost,3),
                    "totalPathCost": round(self.best_solution.totalPathCost,3),
                    "totalTimeCost": round(self.best_solution.totalTimeCost,3),

                    "totalWeatherExtraTime": round(self.best_solution.totalWeatherExtraTime,3),
                    "totalWeatherSafetyRiskKm": round(self.best_solution.totalWeatherSafetyRiskKm,3),
                    "totalWeatherCost": round(self.best_solution.totalWeatherCost,3),

                    "totalShopCost": round(self.best_solution.totalShopCost,3),
                    "totalDepotCost": round(self.best_solution.totalDepotCost,3),
                    "totalResourceCost": round(self.best_solution.totalResourceCost,3),

                    "totalIncome": round(self.best_solution.totalIncome,3),
                    "forgottenTaskCost": round(self.best_solution.forgottenTaskCost,3),
                    "weight": round(self.best_solution.weight,3),
                    "time": round(time,3),
                    "destroy": self.operators.weights_destroy,
                    "repair": self.operators.weights_repair
                    }
            

            writer.writerow(row)

            
        outfile.close()

        weather_file = urls.data_collection_curr
        file_exists = os.path.exists(weather_file)

        with open(weather_file, 'a', newline='', encoding='utf-8') as outfile: 
            fieldnames = ["iteration","totalMonetaryCost","totalPathCost","totalTimeCost",
                            "totalWeatherExtraTime","totalWeatherSafetyRiskKm","totalWeatherCost",
                            "totalShopCost","totalDepotCost","totalResourceCost",
                            "totalIncome","forgottenTaskCost","weight","time","destroy","repair"]
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
            
            if not file_exists:
                writer.writeheader()
            time = self.end_time-self.start_time
            row = {
                    "iteration": self.iteration,
                    "totalMonetaryCost": round(self.current_solution.totalMonetaryCost,3),
                    "totalPathCost": round(self.current_solution.totalPathCost,3),
                    "totalTimeCost": round(self.current_solution.totalTimeCost,3),

                    "totalWeatherExtraTime": round(self.current_solution.totalWeatherExtraTime,3),
                    "totalWeatherSafetyRiskKm": round(self.current_solution.totalWeatherSafetyRiskKm,3),
                    "totalWeatherCost": round(self.current_solution.totalWeatherCost,3),

                    "totalShopCost": round(self.current_solution.totalShopCost,3),
                    "totalDepotCost": round(self.current_solution.totalDepotCost,3),
                    "totalResourceCost": round(self.current_solution.totalResourceCost,3),

                    "totalIncome": round(self.current_solution.totalIncome,3),
                    "forgottenTaskCost": round(self.current_solution.forgottenTaskCost,3),
                    "weight": round(self.current_solution.weight,3),
                    "time": round(time,3),
                    "destroy": self.operators.weights_destroy,
                    "repair": self.operators.weights_repair
                    }
            

            writer.writerow(row)

            
        outfile.close()

        weather_file = urls.data_collection_new
        file_exists = os.path.exists(weather_file)

        with open(weather_file, 'a', newline='', encoding='utf-8') as outfile: 
            fieldnames = ["iteration","totalMonetaryCost","totalPathCost","totalTimeCost",
                            "totalWeatherExtraTime","totalWeatherSafetyRiskKm","totalWeatherCost",
                            "totalShopCost","totalDepotCost","totalResourceCost",
                            "totalIncome","forgottenTaskCost","weight","time","destroy","repair"]
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
            
            if not file_exists:
                writer.writeheader()
            time = self.end_time-self.start_time
            row = {
                    "iteration": self.iteration,
                    "totalMonetaryCost": round(self.new_solution.totalMonetaryCost,3),
                    "totalPathCost": round(self.new_solution.totalPathCost,3),
                    "totalTimeCost": round(self.new_solution.totalTimeCost,3),

                    "totalWeatherExtraTime": round(self.new_solution.totalWeatherExtraTime,3),
                    "totalWeatherSafetyRiskKm": round(self.new_solution.totalWeatherSafetyRiskKm,3),
                    "totalWeatherCost": round(self.new_solution.totalWeatherCost,3),

                    "totalShopCost": round(self.new_solution.totalShopCost,3),
                    "totalDepotCost": round(self.new_solution.totalDepotCost,3),
                    "totalResourceCost": round(self.new_solution.totalResourceCost,3),

                    "totalIncome": round(self.new_solution.totalIncome,3),
                    "forgottenTaskCost": round(self.new_solution.forgottenTaskCost,3),
                    "weight": round(self.new_solution.weight,3),
                    "time": round(time,3),
                    "destroy": self.operators.weights_destroy,
                    "repair": self.operators.weights_repair
                    }
            

            writer.writerow(row)

            
        outfile.close()

    def initialize(self):
        self.iteration = "construct" + "shop:"+ str(SHOP_TEST) + " depot:" + str(DEPOT_TEST) + " weather:" + str(WEATHER_TEST)
        self.start_time = time.time()
        self.readData() # *
        self.construct() # *
        self.end_time = time.time()
        self.saveData()
        #return self.best_solution
    
        
        #while time.time() - start_time <= self.run_time:
        #    pass
        #return self.best_solution
        for i in range(50):
            self.iteration = str(i)
            self.start_time = time.time()
            print("before 2nd print")

            self.selectOperators()

            
            #print(self.unassigned_tasks)
            #print(self.current_solution)
            #if len(self.unassigned_tasks)== 0:
            #    return False
            self.generateNewSolution()

            self.new_solution.updateCosts_Income(self.distances,self.tasks, self.unassigned_tasks, self.weather)


            print("moneys")
            print(self.new_solution.weight)
            print(self.current_solution.weight)
            print(self.best_solution.weight)



            if self.current_solution.weight < self.new_solution.weight:
                self.score = 1
            else:
                self.score = 3
            
            if self.new_solution.weight < self.best_solution.weight:
                self.best_solution = self.new_solution
                self.score = 4

            if self.acceptSimulatedAnnealingFunction():
                self.current_solution = self.new_solution
                self.current_unassigned_tasks = deepcopy(self.unassigned_tasks)
            else:
                self.unassigned_tasks = deepcopy(self.current_unassigned_tasks)

            self.updateWeights()
            self.simulatedAnnealing_temperature *= self.simulatedAnnealing_cooling
            self.end_time = time.time()
            self.saveData()

        self.distances.cache()

        print(self.current_solution)
        return self.best_solution


    def __str__(self):
        pass


if __name__ == "__main__":
    algorithm = ALNS_ALgorithm()
    solution = algorithm.initialize()
    print(solution)

