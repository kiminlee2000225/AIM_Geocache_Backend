from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from xml.etree import ElementTree as ET

app = Flask(__name__, static_url_path='', static_folder='frontend/build')
CORS(app)
api = Api(app)

# Read the given file "aim.geocaches.gpx" and parse it.
gpx_file = open('aim.geocaches.gpx', 'r')
gpx_file_xml = ET.parse(gpx_file).getroot()
waypoints = []
for wpt in gpx_file_xml.findall('wpt'):
    name = wpt.find('./name').text
    hash = wpt.find('./hash').text
    waypoint = [float(wpt.attrib['lat']), float(
        wpt.attrib['lon']), name,  hash]
    waypoints.append(waypoint)

# Create a new file "foundGeocacheWaypoints.xml" that will store the found waypoints by the user.
root = ET.Element('waypoints')
tree = ET.ElementTree(root)
with open('foundGeocacheWaypoints.xml', 'wb') as f:
    tree.write(f)

# POST api call for when a waypoint is found by the user.
# Given the lat, lng, name, and hash values for a found waypoint, store the waypoint
# in the file "foundGeocacheWaypoints.xml" with the same format as the gpx file.
@app.route("/geocacheFound/<lat>/<lng>/<name>/<hash>", methods=['POST'])
def waypointFound(lat, lng, name, hash):
    if lat is None or lng is None or name is None or hash is None:
        return jsonify({'resultStatus': 'FAIL', "message": "Arguments for lat, lng, name, and/or hash is not correctly sent."})

    try:
        foundGeocacheWaypointsFile = open('foundGeocacheWaypoints.xml', 'r')
        fileRoot = ET.parse(foundGeocacheWaypointsFile).getroot()

        for wpt in fileRoot.findall('wpt'):
            currHash = wpt.find('./hash').text
            if hash == currHash:
                return jsonify({'resultStatus': 'SUCCESS', "message": "The found waypoint is already saved as found."})

        wpt = ET.SubElement(fileRoot, 'wpt', lat=lat, lng=lng)
        # Replace '@@' as '/' since '/' cannot be used in a REST api.
        wayPointName = name.replace('@@', '/')
        wptName = ET.SubElement(wpt, 'name')
        wptName.text = wayPointName
        wptHash = ET.SubElement(wpt, 'hash')
        wptHash.text = hash
        tree = ET.ElementTree(fileRoot)
        with open('foundGeocacheWaypoints.xml', 'wb') as f:
            tree.write(f)

    except (ET.ParseError, TypeError, FileNotFoundError):
        return jsonify({'resultStatus': 'FAIL', "message": "Error with parsing, typing, and/or file not found."})

    return jsonify({'resultStatus': 'SUCCESS', "message": "Waypoint found successfully saved."})

# GET api call for the frontend to retrieve the waypoints that has been found by the user.
# Find and parse the waypoints in "foundGeocacheWaypoints.xml" to send to the frontend.
@app.route("/geocacheFoundWaypoints", methods=['GET'])
def geocacheFoundWaypoints():
    try:
        foundGeocacheWaypointsFile = open('foundGeocacheWaypoints.xml', 'r')
        fileRoot = ET.parse(foundGeocacheWaypointsFile).getroot()

        waypoints = []
        for wpt in fileRoot.findall('wpt'):
            name = wpt.find('./name').text
            hash = wpt.find('./hash').text
            waypoint = {'lat': float(wpt.attrib['lat']), 'lng': float(wpt.attrib['lng']),
                        'name': name, 'hash': hash}
            waypoints.append(waypoint)

    except (ET.ParseError, TypeError, FileNotFoundError):
        return jsonify({'resultStatus': 'FAIL', "message": "Error with parsing, typing, and/or file not found."})

    return jsonify({'resultStatus': 'SUCCESS', "message": waypoints})

# GET api call for the frontend to retrieve 15 visible waypoints, given the boundaries of the map.
# northEastLat, northEastLat, southWestLat, and southWestLng represent the boundaries of the map
# as a box. Find and parse the waypoints in "aim.geocaches.gpx" to send to the frontend.
@app.route("/geocacheWaypoints/<northEastLat>/<northEastLng>/<southWestLat>/<southWestLng>", methods=['GET'])
def waypointData(northEastLat, northEastLng, southWestLat, southWestLng):
    if northEastLat is None or northEastLng is None or southWestLat is None or southWestLng is None:
        return jsonify({'resultStatus': 'FAIL', "message": "NorthEast and/or SouthWest boundaries are missing."})

    pointList = []
    counter = 0
    for waypoint in waypoints:
        latitude = waypoint[0]
        longitude = waypoint[1]
        name = waypoint[2]
        hash = waypoint[3]
        if counter >= 15:
            break
        if latitude <= float(northEastLat) and longitude <= float(northEastLng) and latitude >= float(southWestLat) and longitude >= float(southWestLng):
            counter += 1
            point = {'lat': latitude, 'lng': longitude,
                     'name': name, 'hash': hash}
            pointList.append(point)

    return jsonify({'resultStatus': 'SUCCESS', "message": pointList})
