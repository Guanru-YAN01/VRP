import pandas as pd
from helper_functions import time_to_minutes
from data_structures import Stop

# ================== Data Reading and Stop List Construction ==================

def read_data():
    """
    Reads the following CSV files:
      - new_1.csv: Site data (Site_id, Lng, Lat)
      - new_2.csv: Spot data (Spot_id, Lng, Lat)
      - new_3.csv: Shop data (Shop_id, Lng, Lat)
      - new_4.csv: E-commerce orders (Order_id, Spot_id, Site_id, Num)
      - new_5.csv: O2O orders (Order_id, Spot_id, Shop_id, Pickup_time, Delivery_time, Num)
      - new_6.csv: Courier list (Courier_id)
    """
    sites = pd.read_csv("./Dataset/new_1.csv")
    spots = pd.read_csv("./Dataset/new_2.csv")
    shops = pd.read_csv("./Dataset/new_3.csv")
    ecommerce_orders = pd.read_csv("./Dataset/new_4.csv")
    o2o_orders = pd.read_csv("./Dataset/new_5.csv")
    couriers = pd.read_csv("./Dataset/new_6.csv")
    return sites, spots, shops, ecommerce_orders, o2o_orders, couriers

def build_stop_lists(sites, spots, shops, ecommerce_orders, o2o_orders):
    """
    Constructs stops for orders.
      - For e-commerce orders: create a delivery stop (assumes packages are preloaded at the site).
      - For O2O orders: create a pickup stop (from shop) and a delivery stop (to spot).
    Returns two lists:
      - ecommerce_stops: list of Stop objects.
      - o2o_stop_pairs: list of tuples (pickup_stop, delivery_stop).
    """
    # Build lookup dictionaries
    site_dict = {row['Site_id']: (row['Lat'], row['Lng']) for _, row in sites.iterrows()}
    spot_dict = {row['Spot_id']: (row['Lat'], row['Lng']) for _, row in spots.iterrows()}
    shop_dict = {row['Shop_id']: (row['Lat'], row['Lng']) for _, row in shops.iterrows()}
    
    ecommerce_stops = []
    for _, row in ecommerce_orders.iterrows():
        spot_id = row['Spot_id']
        lat, lng = spot_dict[spot_id]
        # Delivery must be done by 20:00 (720 minutes from 08:00)
        stop = Stop(location_id=spot_id, lat=lat, lng=lng,
                    stop_type="ecommerce_delivery",
                    order_id=row['Order_id'],
                    packages=row['Num'],
                    earliest=0, latest=720)
        ecommerce_stops.append(stop)
    
    o2o_stop_pairs = []
    for _, row in o2o_orders.iterrows():
        # Create pickup stop from shop
        shop_id = row['Shop_id']
        shop_lat, shop_lng = shop_dict[shop_id]
        pickup = Stop(location_id=shop_id, lat=shop_lat, lng=shop_lng,
                      stop_type="shop",
                      order_id=row['Order_id'],
                      packages=row['Num'],
                      earliest=time_to_minutes(row['Pickup_time']),
                      latest=720,  # pickup must occur before end of shift
                      paired_order_id=row['Order_id'])
        # Create delivery stop to spot
        spot_id = row['Spot_id']
        spot_lat, spot_lng = spot_dict[spot_id]
        delivery = Stop(location_id=spot_id, lat=spot_lat, lng=spot_lng,
                        stop_type="delivery",
                        order_id=row['Order_id'],
                        packages=row['Num'],
                        earliest=0,
                        latest=time_to_minutes(row['Delivery_time']),
                        paired_order_id=row['Order_id'])
        o2o_stop_pairs.append((pickup, delivery))
    
    return ecommerce_stops, o2o_stop_pairs