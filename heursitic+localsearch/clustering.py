from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

def cluster_stops(stops, n_clusters=20, random_state=42, save_map=False):
    delivery_stops = [stop for stop in stops if stop.stop_type in ("ecommerce_delivery", "delivery")]

    coords = [(stop.lat, stop.lng) for stop in delivery_stops]
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    labels = kmeans.fit_predict(coords)

    # Attach cluster ID to each delivery stop
    for stop, label in zip(delivery_stops, labels):
        stop.cluster_id = label

    if save_map:
        _plot_clusters(delivery_stops, labels, kmeans.cluster_centers_)

    return stops, kmeans


def _plot_clusters(stops, labels, centroids):
    x = [stop.lng for stop in stops]
    y = [stop.lat for stop in stops]
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(x, y, c=labels, cmap="tab20", s=10)
    plt.scatter(centroids[:, 1], centroids[:, 0], c='black', marker='x', label="Centroids")
    plt.title("K-Means Clustering of Delivery Stops")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.colorbar(scatter, label="Cluster ID")
    plt.legend()
    plt.savefig("cluster_map.png")
    print("✅ Saved cluster map as cluster_map.png")
