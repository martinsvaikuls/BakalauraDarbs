import requests

OSRM_URL = "http://localhost:5000"


def get_route(coord_a, coord_b):

    lat1, lon1 = coord_a
    lat2, lon2 = coord_b

    url = (
        f"{OSRM_URL}/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
        f"?overview=false"
    )

    response = requests.get(url, timeout=3)

    data = response.json()

    route = data["routes"][0]

    return (
        route["distance"] / 1000,
        route["duration"] / 60
    )


def get_geometry(coord_a, coord_b):

    lat1, lon1 = coord_a
    lat2, lon2 = coord_b

    url = (
        f"{OSRM_URL}/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
        f"?overview=full&geometries=geojson"
    )

    response = requests.get(url, timeout=5)

    data = response.json()

    route = data["routes"][0]

    return route["geometry"]