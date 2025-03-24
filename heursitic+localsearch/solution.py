import random
import copy
import csv
from tqdm import tqdm
import contextily as ctx
import matplotlib.pyplot as plt
import numpy as np
import imageio
from data_structures import Route, Stop
from helper_functions import travel_time, service_time, compute_distance

# ================== Parameters ==================
SPEED = 15  # km/h
SPEED = SPEED / 60.0  # km/min, e.g., 0.25 km/min
MAX_CAPACITY = 140  # Maximum capacity for O2O orders (packages)
MAX_WORK_MINUTES = 720  # Courier shift: 12 hours (from 08:00 to 20:00)

# ================== Visualization Function ==================
def visualize_routes(routes, title="Current Routes"):
    plt.clf()  # Clear current figure
    ax = plt.gca()
    
    # Plot each route with small markers and lines
    for route in routes.values():
        lats = [stop.lat for stop in route.stops]
        lngs = [stop.lng for stop in route.stops]
        ax.plot(lngs, lats, marker='o', linestyle='-', linewidth=1, markersize=3, alpha=0.5)
    
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title)
    
    # Determine plot extents from all stops to ensure the basemap covers the area
    all_lats = []
    all_lngs = []
    for route in routes.values():
        all_lats.extend([stop.lat for stop in route.stops])
        all_lngs.extend([stop.lng for stop in route.stops])
    if all_lats and all_lngs:
        margin = 0  # Adjust as needed for a small border around the points
        ax.set_xlim(min(all_lngs) - margin, max(all_lngs) + margin)
        ax.set_ylim(min(all_lats) - margin, max(all_lats) + margin)
    
    # Add a clean background map using CartoDB Positron style.
    # The crs parameter tells contextily that our data is in EPSG:4326.
    try:
        ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.CartoDB.Positron)
    except Exception as e:
        print("Error adding basemap:", e)
    
    plt.pause(0.1)  # Pause briefly to update the figure

# ================== Initial Solution Construction ==================
def initial_solution(sites, ecommerce_stops, o2o_stop_pairs, couriers, visualize=False):
    """
    Constructs an initial solution using a greedy insertion method.
      - Each courier starts at a randomly chosen site.
      - Ecommerce orders (delivery stops) are appended if feasible.
      - O2O orders (pickup then delivery) are appended as a pair.
    Incorporates a progress bar (tqdm) and live visualization.
    """
    routes = {}
    # Assign each courier a starting site (depot)
    for _, row in couriers.iterrows():
        courier_id = row['Courier_id']
        site_row = sites.sample(1).iloc[0]
        lat, lng = site_row['Lat'], site_row['Lng']
        start_stop = Stop(location_id=site_row['Site_id'], lat=lat, lng=lng,
                          stop_type="site", order_id=None, packages=0,
                          earliest=0, latest=720)
        start_stop.arrival = 0
        start_stop.departure = 0
        routes[courier_id] = Route(courier_id, start_stop)
    
    # Ecommerce orders insertion with progress bar and visualization
    count = 0
    for order_stop in tqdm(ecommerce_stops, desc="Inserting ecommerce orders"):
        best_route = None
        best_increase = float('inf')
        for route in routes.values():
            candidate = copy.deepcopy(route)
            candidate.stops.append(copy.deepcopy(order_stop))
            total_time, feasible, penalty = recalc_route_times(candidate)
            cost = total_time + penalty
            if feasible and cost < best_increase:
                best_increase = cost
                best_route = route
        if best_route is not None:
            best_route.stops.append(order_stop)
        count += 1

        if visualize:
        # Visualize every 10 insertions
            if count % 10 == 0:
                visualize_routes(routes, title=f"Ecommerce Insertion - {count} orders inserted")
    
    # O2O orders insertion with progress bar and visualization
    count = 0
    for pickup_stop, delivery_stop in tqdm(o2o_stop_pairs, desc="Inserting O2O orders"):
        best_route = None
        best_increase = float('inf')
        for route in routes.values():
            candidate = copy.deepcopy(route)
            candidate.stops.append(copy.deepcopy(pickup_stop))
            candidate.stops.append(copy.deepcopy(delivery_stop))
            total_time, feasible, penalty = recalc_route_times(candidate)
            cost = total_time + penalty
            if feasible and cost < best_increase:
                best_increase = cost
                best_route = route
        if best_route is not None:
            best_route.stops.append(pickup_stop)
            best_route.stops.append(delivery_stop)
        count += 1

        if visualize:
            # Visualize every 5 O2O insertions
            if count % 5 == 0:
                visualize_routes(routes, title=f"O2O Insertion - {count} orders inserted")
    
    # Update timings for all routes
    for route in routes.values():
        recalc_route_times(route)
    
    return routes

# ================== Route Evaluation and Feasibility ==================

def recalc_route_times(route):
    """
    Recalculate arrival and departure times along the route.
    Simulate load changes and check for constraint violations.
    Returns: (total_time, feasible, penalty)
    """
    current_load = 0
    feasible = True
    penalty = 0
    # Initialize first stop (site)
    route.stops[0].arrival = 0
    route.stops[0].departure = 0
    for i in range(1, len(route.stops)):
        prev = route.stops[i-1]
        stop = route.stops[i]
        # Compute travel time
        d = compute_distance(prev.lat, prev.lng, stop.lat, stop.lng)
        t_time = travel_time(d)
        arrival = prev.departure + t_time
        # If arriving before earliest, wait
        if arrival < stop.earliest:
            arrival = stop.earliest
        stop.arrival = arrival
        # Service time depends on stop type
        if stop.stop_type in ["delivery", "ecommerce_delivery", "shop"]:
            s_time = service_time(stop.packages)
        else:
            s_time = 0
        stop.departure = arrival + s_time
        
        # Update load for O2O orders:
        if stop.stop_type == "shop":
            current_load += stop.packages
            if current_load > MAX_CAPACITY:
                feasible = False
                penalty += (current_load - MAX_CAPACITY) * 100
        elif stop.stop_type == "delivery":
            # For O2O, ensure pickup happened first; then reduce load.
            current_load -= stop.packages
            if current_load < 0:
                feasible = False
                penalty += 1000
        
        # Check time window violation
        if stop.latest is not None and stop.arrival > stop.latest:
            feasible = False
            penalty += (stop.arrival - stop.latest) * 50
    
    total_time = route.stops[-1].departure
    if total_time > MAX_WORK_MINUTES:
        feasible = False
        penalty += (total_time - MAX_WORK_MINUTES) * 100
    return total_time, feasible, penalty

def route_cost(route):
    """Compute route cost as total time plus any penalties."""
    total_time, _, penalty = recalc_route_times(route)
    return total_time + penalty

def is_feasible_route(route):
    """Returns True if the route meets all constraints."""
    _, feasible, _ = recalc_route_times(route)
    return feasible

# ================== Local Search: 2-opt and Swap Moves ==================

def two_opt(route):
    """
    Apply 2-opt moves to a route.
    Reverse segments and accept the move if it reduces cost and keeps feasibility.
    """
    best_route = copy.deepcopy(route)
    best_cost = route_cost(best_route)
    improved = True
    while improved:
        improved = False
        n = len(best_route.stops)
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                candidate = copy.deepcopy(best_route)
                candidate.stops[i:j+1] = list(reversed(candidate.stops[i:j+1]))
                if is_feasible_route(candidate):
                    cand_cost = route_cost(candidate)
                    if cand_cost < best_cost:
                        best_route = candidate
                        best_cost = cand_cost
                        improved = True
        # Loop until no improvement is found
    return best_route

def intra_route_swap(route):
    """
    Try swapping two stops (except the start) and accept if it improves the cost.
    Also check that pickup-delivery precedence is maintained.
    """
    best_route = copy.deepcopy(route)
    best_cost = route_cost(best_route)
    n = len(best_route.stops)
    for i in range(1, n):
        for j in range(i + 1, n):
            candidate = copy.deepcopy(best_route)
            candidate.stops[i], candidate.stops[j] = candidate.stops[j], candidate.stops[i]
            # Check that for each O2O order, the shop (pickup) comes before its delivery.
            valid = True
            order_positions = {}
            for idx, stop in enumerate(candidate.stops):
                if stop.order_id is not None and stop.paired_order_id is not None:
                    if stop.stop_type == "shop":
                        order_positions[stop.order_id] = idx
                    elif stop.stop_type == "delivery":
                        if stop.order_id in order_positions and idx < order_positions[stop.order_id]:
                            valid = False
                            break
            if not valid:
                continue
            if is_feasible_route(candidate):
                cand_cost = route_cost(candidate)
                if cand_cost < best_cost:
                    best_route = candidate
                    best_cost = cand_cost
    return best_route

def local_search(routes):
    """
    Apply local search moves (2-opt and intra-route swap) to each route.
    """
    improved_routes = {}
    for courier_id, route in tqdm(list(routes.items()), desc="Local search on routes"):
        new_route = two_opt(route)
        new_route = intra_route_swap(new_route)
        improved_routes[courier_id] = new_route
    return improved_routes

def save_schedule_to_csv(routes, filename="heuristic+localsearch_schedule.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Courier_id", "Location_id", "Stop_Type", "Arrival_time", "Departure_time", "Amount", "Order_id"])
        for courier_id, route in routes.items():
            # Sort stops by arrival time for clarity
            route.stops.sort(key=lambda s: s.arrival if s.arrival is not None else float('inf'))
            for stop in route.stops:
                arr = int(round(stop.arrival)) if stop.arrival is not None else 0
                dep = int(round(stop.departure)) if stop.departure is not None else 0
                writer.writerow([courier_id, stop.location_id, stop.stop_type, arr, dep, stop.packages, stop.order_id])
    print(f"Schedule saved to {filename}")