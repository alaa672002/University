import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from datetime import datetime, timedelta
import googlemaps

# Read data from CSV files
vehicles_data = pd.read_csv('vehicle_data.csv.txt')
order_data = pd.read_csv('order_data.csv.txt')

# Define constants
DEPOT_LATITUDE = 52.504911987650644  # Replace with the actual coordinates of your depot
DEPOT_LONGITUDE = -2.021540016183789 
MAX_VEHICLES = len(vehicles_data)
MAX_ORDERS = len(order_data)
SERVICE_TIME = 15  # in minutes
MAX_ROUTE_DISTANCE = 1000  # Maximum allowed route distance in miles
BREAK_TIME = 45  # in minutes
MAX_WORK_HOURS = 9  # 4.5 hours driving + 45 minutes break

# Set your Google Maps API key
GOOGLE_MAPS_API_KEY = 'AIzaSyCPkBci2qNZIXC9_riaSGapcErAzfJMKDo'
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

transit_callback_index = None
# Function to convert postcodes into distances using the Google Maps Distance Matrix API
def get_distance_matrix(locations):
    distance_matrix = []

    for origin in locations:
        row = []
        for destination in locations:
            result = gmaps.distance_matrix(
                origins=origin,
                destinations=destination,
                mode='driving',
                departure_time=datetime.now(),
                traffic_model='best_guess',
            )
            distance = result['rows'][0]['elements'][0]['distance']['value'] / 1609.34  # Convert meters to miles
            row.append(distance)

        distance_matrix.append(row)

    return distance_matrix

# Function to calculate time windows for each order
def calculate_time_windows():
    time_windows = []
    start_time = datetime.strptime('06:00', '%H:%M')

    for _, order in order_data.iterrows():
        delivery_time = start_time + timedelta(minutes=order['Stop_Number'] * SERVICE_TIME)
        end_time = delivery_time + timedelta(hours=MAX_WORK_HOURS)
        time_windows.append((int(delivery_time.timestamp()), int(end_time.timestamp())))

    return time_windows

# Function to define the routing problem
def create_data_model():
    data = {}
    time_windows = calculate_time_windows()

    data['distance_matrix'] = get_distance_matrix(order_data['Location'])
    data['time_windows'] = time_windows
    data['num_vehicles'] = MAX_VEHICLES
    data['depot'] = 0

    return data

# Function to add constraints to the routing model
def add_constraints(routing, manager, data):
    global transit_callback_index

    for vehicle_id in range(data['num_vehicles']):
        index = manager.NodeToIndex(vehicle_id)
        slack_max = [MAX_ROUTE_DISTANCE] * len(data['distance_matrix'])
      
        routing.AddDimension(
            transit_callback_index,
            0,  # no slack
            MAX_ROUTE_DISTANCE,  # vehicle maximum travel distance
            True,  # start cumul to zero
            'Distance'
        )
        routing.AddDimension(
            transit_callback_index,
            0,  # no slack
            MAX_WORK_HOURS * 60,  # maximum working time in minutes
            True,  # start cumul to zero
            'Time'
        )

        routing.SetArcCostEvaluatorOfVehicle(transit_callback_index, vehicle_id)

        routing.AddBreak(
            4 * 60 * 60,  # 4.5 hours in seconds
            5 * 60 * 60,  # 5 hours in seconds
            0  # unused, break duration is set in the model parameters
        )
        routing.AddBreak(
            9 * 60 * 60,  # 9 hours in seconds
            9 * 60 * 60 + BREAK_TIME * 60,  # 9.75 hours in seconds
            0  # unused, break duration is set in the model parameters
        )

        routing.AddVariableMinimizedByFinalizer(
            manager.CumulVar(index, 'Time')
        )
        routing.AddVariableMinimizedByFinalizer(
            manager.CumulVar(index, 'Distance')
        )

# Function to print the solution
def print_solution(data, manager, routing, solution, vehicles_data, order_data):
    total_miles = 0
    
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_time = 0
        current_weight = vehicle_data.at[vehicle_id, 'Weight_limit']

        plan_output = f"Route for Vehicle {vehicle_id}:\n"
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            next_node_index = manager.IndexToNode(
                solution.Value(routing.NextVar(index))
            )
            
            # Accumulate the distance of the route
            route_distance += routing.GetArcCostForVehicle(node_index, next_node_index, vehicle_id)
            
            # Update the current weight of the vehicle based on the order
            order_index = manager.IndexToNode(index) - 1  # Assuming the first node is the depot
            if order_index >= 0:  # Skip the depot
                order_weight = order_data.at[order_index, 'Total_Weight']
                order_type = order_data.at[order_index, 'Order_Type']

                if order_type == 'delivery':
                    current_weight -= order_weight
                elif order_type == 'collection':
                    current_weight += order_weight

            # Accumulate the time of the route
            route_time += routing.GetArcCostForVehicle(node_index, next_node_index, vehicle_id, 'Time')

            # ... (other output related code)

            index = solution.Value(routing.NextVar(index))

        # Update the total miles
        total_miles += route_distance

        # Print the total distance and time for the route
        plan_output += f"Distance of the route: {route_distance} miles\n"
        plan_output += f"Time of the route: {route_time / 60} hours\n"
        plan_output += f"Current Weight: {current_weight} kg\n"

        print(plan_output)

    # Print the total miles for all vehicles
    print(f"Total Miles for All Vehicles: {total_miles} miles")

# Main function to solve the CVRP using Google OR-Tools
def solve_cvrp():
    # Step 1: Create the data model
    data = create_data_model()

    # Step 2: Create the routing index manager and routing model
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    # Step 3: Set up the distance callback and time window constraints
    def distance_callback(from_index, to_index):
        return data['distance_matrix'][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Step 4: Add constraints
    add_constraints(routing, manager, data)

    # Step 5: Set the search parameters
    search_parameters = pywrapcp.Default
    
    # Step 6: Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Step 7: Print the solution
    if solution:
        print_solution(data, manager, routing, solution, vehicles_data, order_data)
    else:
        print("No solution found.")

# Call the main function to solve the CVRP
solve_cvrp()
