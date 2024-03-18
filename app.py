# app.py
import asyncio
from math import atan2, cos, radians, sin, sqrt
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_swagger_ui import get_swaggerui_blueprint
import googlemaps
from datetime import datetime
import polyline
from firebase_admin import firestore, initialize_app, credentials
import requests
from config import API_KEY
from flask_cors import CORS, cross_origin
from geopy.distance import geodesic
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

# from apscheduler.schedulers.background import BackgroundScheduler
gmaps = googlemaps.Client(key=API_KEY)

app = Flask(__name__)
CORS(app)
api = Api(app)

# Configure Swagger UI
SWAGGER_URL = '/swagger'
API_URL = "/static/swagger.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "CoDrive"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

cred = credentials.Certificate("firebase-admin.json")
initialize_app(cred)

db = firestore.client()

userRef = db.collection("Users")
vehicleRef = db.collection("Vehicles")
reviewRef = db.collection("Reviews")
rideRef = db.collection("Rides")

# scheduler = BackgroundScheduler()

def printHello():
    print("Hello")
    
# scheduler.add_job(printHello, 'interval', seconds=10)

# scheduler.start()

@app.route('/hello')
def hello():
    return {"members":["member1","member2","member5"]}

# api.add_resource(hello, '/hello')

def get_vehicle(vehicle_id):
    docRef = vehicleRef.document(vehicle_id)
    doc = docRef.get()
    if doc.exists:
        vehicle = doc.to_dict()
        vehicle["Id"] = vehicle_id
        return vehicle
    else:
        return None
    
def get_reviewer(user_id):
    docRef = userRef.document(user_id)
    doc = docRef.get()
    if doc.exists:
        data = doc.to_dict()
        return {
            "Name": f"{data['FirstName']} {data['LastName']}",
            "ProfileUrl": data['ProfileUrl'],
            "Id": user_id
        }
    else:
        return None 

def get_review(review_id):
    docRef = reviewRef.document(review_id)
    doc = docRef.get()
    if doc.exists:
        data = doc.to_dict()
        data["Id"] = review_id
        data["Reviewer"] = get_reviewer(data["Reviewer"].get().id)
        return data
    else:
        return None
    
def get_driver(user_id):
    docRef = userRef.document(user_id)
    doc = docRef.get()
    if doc.exists:
        data = doc.to_dict()
        return {
            "Name": f"{data['FirstName']} {data['LastName']}",
            "ProfileUrl": data['ProfileUrl'],
            "Id": user_id
        }
    else:
        return None
    
def get_corider(user_id):
    docRef = userRef.document(user_id)
    doc = docRef.get()
    if doc.exists:
        data = doc.to_dict()
        return {
            "Name": f"{data['FirstName']} {data['LastName']}",
            "ProfileUrl": data['ProfileUrl'],
            "Id": user_id
        }
    else:
        return None
    
def get_ride(ride_id):
    docRef = rideRef.document(ride_id)
    doc = docRef.get()
    if doc.exists:
        data = doc.to_dict()
        data["Id"] = ride_id
        if "Driver" in data:
            data["Driver"] = get_driver(data["Driver"].get().id)
        if "Vehicle" in data:
            data["Vehicle"] = get_vehicle(data["Vehicle"].get().id)

        coRidersRef = docRef.collection("CoRiders")
        co_riders = coRidersRef.get()
        co_riders_data = []
        for co_rider in co_riders:
            co_rider_data = co_rider.to_dict()
            if co_rider_data["CoRider"]:
                co_rider_data["CoRider"] = get_corider(co_rider_data["CoRider"].get().id)
                co_riders_data.append(co_rider_data)
        data["CoRiders"] = co_riders_data
        return data
    else:
        return None
    
def get_corider(corider_id):
    docRef = userRef.document(corider_id)
    doc = docRef.get()
    if doc.exists:
        data = doc.to_dict()
        return {
            "Name": f"{data['FirstName']} {data['LastName']}",
            "ProfileUrl": data['ProfileUrl'],
            "Id": corider_id
        }
    else:
        return None
    
def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Difference in latitude and longitude
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance


@app.route('/get_user', methods=['GET'])
def get_user():
    docRef = userRef.document(request.args.get('userId'))
    doc = docRef.get()
    if doc.exists:
        user_data = doc.to_dict()
        user_data["Id"] = doc.id
        if "Reviews" in user_data:
            user_data["Reviews"] = [get_review(ref.get().id) for ref in user_data["Reviews"]]
        if "Vehicles" in user_data:
            user_data["Vehicles"] = [get_vehicle(ref.get().id) for ref in user_data["Vehicles"]]
        del user_data["History"]
        return jsonify(user_data)
    else:
        print("No such document!")
        return None
    
@app.route('/get_history', methods=['GET'])
def get_history():
    docRef = userRef.document(request.args.get('userId'))
    doc = docRef.get()
    if doc.exists:
        user_data = doc.to_dict()
        if "History" in user_data:
            user_data["History"] = [get_ride(ref.get().id) for ref in user_data["History"]]
        
        history_data = user_data["History"]

        return jsonify(history_data)
    else:
        print("No such document!")
        return None

@app.route('/get_directions')
def get_directions():
    try:
        # Get source and destination
        source_lat = float(request.args.get('s1'))
        source_lng = float(request.args.get('s2'))
        destination_lat = float(request.args.get('d1'))
        destination_lng = float(request.args.get('d2'))

        source_str = f"{source_lat},{source_lng}"
        destination_str = f"{destination_lat},{destination_lng}"

        print("Hello", source_str, destination_str)

        # Request directions from Google Maps API
        directions_result = gmaps.directions(
            source_str,
            destination_str,
            mode="driving",  # You can change the mode based on your requirements
            departure_time=datetime.now(),
        )

        # Extract relevant information from the directions result
        route = directions_result[0]['legs'][0]
        steps = route['steps']

        total_distance = route['distance']['text']
        total_duration = route['duration']['text']
        
        # Use arrival_time if available, otherwise, use duration_in_traffic
        eta = route['arrival_time']['text'] if 'arrival_time' in route else route['duration_in_traffic']['text']

        # Extract polyline coordinates
        encoded_polyline = directions_result[0]['overview_polyline']['points']
        decoded_polyline = polyline.decode(encoded_polyline)

        # Additional information
        total_steps = len(steps)

        response_data = {
            'status': 'success',
            'total_distance': total_distance,
            'total_duration': total_duration,
            'eta': eta,
            'polyline_coordinates': decoded_polyline,
            'total_steps': total_steps,
            'steps': [{
                'instruction': step['html_instructions'],
                'distance': step['distance']['text'],
                'duration': step['duration']['text'],
                'start_location': step['start_location'],
                'end_location': step['end_location'],
            } for step in steps],
        }

        return jsonify(response_data)

    except Exception as e:
        # Handle error
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    try:
        data = request.json
        userId = data.get('userId')

        vehicle_data = {
            "FuelType": data.get('fuelType'),
            "SeatingCapcity": data.get('seatingCapacity'),
            "VehicleName": data.get('vehicleName'),
            "VehicleNumber": data.get('vehicleNumber')  
        }

        doc_ref = vehicleRef.document()
        doc_ref.set(vehicle_data)
        doc_id = doc_ref.id


        user_doc = userRef.document(userId)
        user_doc.update({"Vehicles": firestore.ArrayUnion([doc_ref])})

        return jsonify({"message": "Vehicle added successfully", "document_id": doc_id, "data": vehicle_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_places', methods=['GET'])
def get_places():
    query = request.args.get('query')
    src_lat = float(request.args.get('src_lat'))
    src_lng = float(request.args.get('src_lng'))
    url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}'


    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        places = data.get('results', [])

        if not places:
            return jsonify({'error': 'No places found.'}), 404

        results = []
        for place in places:
            place_lat = place['geometry']['location']['lat']
            place_lon = place['geometry']['location']['lng']
            distance = calculate_distance(src_lat, src_lng, place_lat, place_lon)
            place['distance'] = distance
            results.append(place)

        return jsonify({'places': results})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_ride', methods=['GET'])
def start_ride():
    try:
        # data = request.json

        userId = request.args.get('userId')
        vehicleId = request.args.get('vehicleId')
        distance = request.args.get('totalDistance')

        # Source Latitude, Longitude & String
        s_lat = float(request.args.get('s_lat'))
        s_lng = float(request.args.get('s_lng'))
        s_str = request.args.get('s_str')

        # Destination Latitude, Longitude & String
        d_lat = float(request.args.get('d_lat'))
        d_lng = float(request.args.get('d_lng'))
        d_str = request.args.get('d_str')

        isNow = request.args.get('isNow')
        startTime = 0
        if(isNow):
            startTime = SERVER_TIMESTAMP
        else:
            startTime = request.args.get('startTime')

        source = [s_lat, s_lng, s_str]
        destination = [d_lat, d_lng, d_str]

        driver_ref = userRef.document(userId)

        ride_data = {
            "Source": source,
            "Destination": destination,
            "Status": "Started",
            "StartTime": startTime,
            "Driver": driver_ref,
            # "TotalDistance": distance,
            "Vehicle": vehicleRef.document(vehicleId)
        }

        doc_ref = rideRef.document()
        doc_ref.set(ride_data)
        doc_id = doc_ref.id

        user_doc = userRef.document(userId)
        user_doc.update({"History": firestore.ArrayUnion([doc_ref])})

        return jsonify({"message": "Ride started successfully", "document_id": doc_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/join_ride', methods=['GET'])
def join_ride():
    try:
        userId = request.args.get('userId')
        rideId = request.args.get('rideId')

        # Pickup Latitude, Longitude & String
        p_lat = int(request.args.get('p_lat'))
        p_lng = int(request.args.get('p_lng'))
        p_str = request.args.get('p_str')

        # Drop Latitude, Longitude & String
        d_lat = int(request.args.get('d_lat'))
        d_lng = int(request.args.get('d_lng'))
        d_str = request.args.get('d_str')

        pickup = [p_lat, p_lng, p_str]
        drop = [d_lat, d_lng, d_str]

        corider_ref = userRef.document(userId)
        doc_ref = rideRef.document(rideId).collection("CoRiders").document()
        
        ride_data = {
            "Pickup": pickup,
            "Drop": drop,
            "PickupTime": SERVER_TIMESTAMP,
            "DropTime": SERVER_TIMESTAMP,
            "Distance": 1,
            "CoRider": corider_ref,
            "Amount": 30
        }

        doc_ref.set(ride_data)
        doc_id = doc_ref.id

        user_doc = userRef.document(userId)
        user_doc.update({"History": firestore.ArrayUnion([doc_ref])})

        return jsonify({"message": "Ride joined successfully", "document_id": doc_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def fetch_route_coordinates(source_lat, source_lng, destination_lat, destination_lng):
    source_str = f"{source_lat},{source_lng}"
    destination_str = f"{destination_lat},{destination_lng}"
    directions_result = gmaps.directions(
        source_str,
        destination_str,
        mode="driving",  # You can change the mode based on your requirements
        departure_time=datetime.now(),
    )

    # Extract relevant information from the directions result
    if len(directions_result) > 0:
        route = directions_result[0]['legs'][0]
        steps = route['steps']
        encoded_polyline = directions_result[0]['overview_polyline']['points']
        decoded_polyline = polyline.decode(encoded_polyline)
        if len(decoded_polyline) > 0:
            # Insert source coordinates at the beginning
            decoded_polyline.insert(0, (source_lat, source_lng))
            # Append destination coordinates at the end
            decoded_polyline.append((destination_lat, destination_lng))
            return decoded_polyline 
        else:
            return []
    else:
        return []
    

@app.route('/search_rides', methods=['GET'])
def search_rides():
    # Get user's source and destination coordinates from the request
    user_source_lat = float(request.args.get('s_lat'))
    user_source_lng = float(request.args.get('s_lng'))
    user_destination_lat = float(request.args.get('d_lat'))
    user_destination_lng = float(request.args.get('d_lng'))


    # Fetch all ride documents with status "Started" from Firestore
    query = rideRef.where("Status", "==", "Started")
    rides = query.stream()

    # Fetch route coordinates for the user's source and destination from Google Maps Directions API
    user_route_coordinates = fetch_route_coordinates(user_source_lat, user_source_lng, user_destination_lat, user_destination_lng)

    filtered_rides = []
    count = 0

    # Iterate over all rides and filter based on proximity to the user's source and destination coordinates
    results = []
    for ride in rides:
        count = count + 1
        ride_data = ride.to_dict()
        ride_data["Id"] = ride.id

        document_route_coordinates = fetch_route_coordinates(ride_data["Source"][0], ride_data["Source"][1], ride_data["Destination"][0], ride_data["Destination"][1])
        # return jsonify({"Coords": document_route_coordinates, "Data": [ride_data["Source"], ride_data["Destination"]]})

        source_proximity = False
        for lat, lng in document_route_coordinates:
            distance = geodesic((user_source_lat, user_source_lng), (lat, lng)).meters
            if distance <= 1000:
                source_proximity = True
                break

        destination_proximity = False
        for lat, lng in document_route_coordinates:
            distance = geodesic((user_destination_lat, user_destination_lng), (lat, lng)).meters
            if distance <= 1000:
                destination_proximity = True
                break
        # destination_proximity = any(geodesic((user_destination_lat, user_destination_lng), (lat, lng)).meters <= 500 for lat, lng in document_route_coordinates)

    if source_proximity and destination_proximity:
        filtered_rides.append(ride_data)
    
    if(filtered_rides):
        for ride in filtered_rides:
            results.append({
                "Source": ride["Source"], 
                "Destination": ride["Destination"], 
                "Status": ride["Status"],
                "Id": ride["Id"]
            })

    return jsonify({'rides': results})

if __name__ == "__main__":
    app.run(debug=True)

