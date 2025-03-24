# ================== Data Structures ==================

class Stop:
    def __init__(self, location_id, lat, lng, stop_type, order_id=None, packages=0,
                 earliest=0, latest=24*60, paired_order_id=None):
        """
        stop_type: "site" for starting depot, "ecommerce_delivery" for e-commerce deliveries,
                   "shop" for O2O pickup, "delivery" for O2O delivery.
        earliest, latest: time window in minutes from 08:00.
        paired_order_id: used to link a shop pickup with its delivery.
        """
        self.location_id = location_id
        self.lat = lat
        self.lng = lng
        self.stop_type = stop_type
        self.order_id = order_id
        self.packages = packages
        self.earliest = earliest
        self.latest = latest
        self.paired_order_id = paired_order_id  # For O2O orders
        self.arrival = None
        self.departure = None
        self.cluster_id = None

class Route:
    def __init__(self, courier_id, start_stop):
        self.courier_id = courier_id
        self.stops = [start_stop]  # initial depot (site)
    
    def total_time(self):
        if self.stops and self.stops[-1].departure is not None:
            return self.stops[-1].departure
        return 0