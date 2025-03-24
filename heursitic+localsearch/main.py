from tqdm import tqdm
import matplotlib.pyplot as plt
from collections import defaultdict
import pandas as pd

from data_reading_stoplist_construction import read_data, build_stop_lists
from solution import initial_solution, recalc_route_times, local_search, save_schedule_to_csv
from clustering import cluster_stops

# ================== Main Function ==================

def main():
    # 1. Read Data
    sites, spots, shops, ecommerce_orders, o2o_orders, couriers = read_data()
    print("✅ Data reading completed.")
    
    # 2. Build Stop Lists
    ecommerce_stops, o2o_stop_pairs = build_stop_lists(sites, spots, shops, ecommerce_orders, o2o_orders)
    print("✅ Stop lists constructed.")
    
    # 3. Combine delivery stops for clustering
    delivery_stops = ecommerce_stops + [pair[1] for pair in o2o_stop_pairs]

    # 4. Cluster delivery stops (e.g., 20 clusters)
    clustered_stops, kmeans_model = cluster_stops(delivery_stops, n_clusters=8, save_map=True)
    print("✅ Clustering completed and cluster map saved.")
    
    # 5. Group all stops by cluster ID
    stops_by_cluster = defaultdict(list)
    stop_lookup = {stop.order_id: stop for stop in delivery_stops}
    
    for stop in clustered_stops:
        cluster_id = stop.cluster_id
        stops_by_cluster[cluster_id].append(stop)
        
        # If O2O delivery, include its pickup stop
        if stop.stop_type == "delivery":
            # Find the matching pickup
            pickup_stop = next((p for p, d in o2o_stop_pairs if d.order_id == stop.order_id), None)
            if pickup_stop:
                stops_by_cluster[cluster_id].append(pickup_stop)

    # 6. Assign couriers per cluster (for now, assign equally)
    cluster_ids = list(stops_by_cluster.keys())
    courier_ids = couriers['Courier_id'].tolist()
    num_clusters = len(cluster_ids)
    couriers_by_cluster = {
        cluster_id: [cid for i, cid in enumerate(courier_ids) if i % num_clusters == cluster_id]
        for cluster_id in cluster_ids
    }

    # 7. Solve each cluster individually
    final_routes = {}
    for cluster_id in cluster_ids:
        stops_in_cluster = stops_by_cluster[cluster_id]
        cluster_courier_ids = couriers_by_cluster[cluster_id]
        cluster_couriers_df = pd.DataFrame({'Courier_id': cluster_courier_ids})
        cluster_routes = initial_solution(sites, stops_in_cluster, [], cluster_couriers_df, visualize=False)
        improved_cluster_routes = local_search(cluster_routes)
        final_routes.update(improved_cluster_routes)
        print(f"✅ Cluster {cluster_id}: routes optimized with {len(cluster_courier_ids)} couriers.")

    # 8. Evaluate and print summary of routes
    total_time = 0
    for courier_id, route in tqdm(final_routes.items(), desc="Evaluating routes"):
        t_time, feasible, penalty = recalc_route_times(route)
        print(f"Courier {courier_id}: Total Time = {t_time:.2f} min, Feasible: {feasible}, Penalty: {penalty}")
        total_time += t_time
    print(f"✅ Total time for all routes: {total_time:.2f} minutes")
    
    # 9. Save final schedule to CSV
    save_schedule_to_csv(final_routes)

# ================== Run Script ==================

if __name__ == "__main__":
    plt.ion()  # Enable interactive mode for live updates
    try:
        main()
    except KeyboardInterrupt:
        print("❌ Program interrupted. Closing plot...")
    finally:
        plt.ioff()
        plt.close('all')
