import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import atexit

# Create a tile source for the basemap
tiler = cimgt.Stamen('terrain-background')  # Other options: 'toner', 'watercolor'
# Use a global axis with a PlateCarree projection (for lat/lon)
proj = ccrs.PlateCarree()

def visualize_routes(routes, title="Current Routes"):
    # Create a new figure with Cartopy projection
    fig = plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=proj)
    
    # Collect all longitudes and latitudes for determining extent
    all_lngs, all_lats = [], []
    for route in routes.values():
        lngs = [stop.lng for stop in route.stops]
        lats = [stop.lat for stop in route.stops]
        all_lngs.extend(lngs)
        all_lats.extend(lats)
    
    if all_lngs and all_lats:
        margin = 0.05
        min_lng, max_lng = min(all_lngs), max(all_lngs)
        min_lat, max_lat = min(all_lats), max(all_lats)
        ax.set_extent([min_lng - margin, max_lng + margin, min_lat - margin, max_lat + margin], crs=proj)
    
    # Add the basemap image
    ax.add_image(tiler, 12)  # Zoom level 12 (adjust as needed)
    
    # Plot each route on top of the basemap
    for route in routes.values():
        lngs = [stop.lng for stop in route.stops]
        lats = [stop.lat for stop in route.stops]
        # Plot route line with markers
        ax.plot(lngs, lats, marker='o', linestyle='-', linewidth=1, markersize=1, transform=proj)
        # Annotate depot
        # if route.stops:
        #     ax.text(lngs[0], lats[0], "Depot", color="blue", fontsize=9, transform=proj)
        #     for idx, stop in enumerate(route.stops[1:], start=1):
        #         label = str(stop.order_id) if stop.order_id is not None else ""
        #         ax.text(lngs[idx], lats[idx], label, fontsize=8, transform=proj)
    
    plt.title(title)
    plt.pause(0.1)
    plt.draw()
    plt.show(block=False)  # Non-blocking show

# Register an exit handler to close all figures when the program exits
atexit.register(plt.close, 'all')
