import json
from collections import deque

with open("stations_routes.json", "r") as f:
    raw_stations_data = json.load(f)
    all_services = {}
    all_stations = set()
    all_stations_service_changes = {}
    adjacency = {}

    for provider, provider_data in raw_stations_data.items():
        for service, directions in provider_data.items():
            all_services[service] = directions
            for direction in directions:
                for index, station in enumerate(direction):
                    all_stations.add(station)
                    all_stations_service_changes.setdefault(station, set()).add(service)
                    adjacency.setdefault(station, set())
                    if index > 0:
                        previous_station = direction[index - 1]
                        adjacency[station].add(previous_station)
                        adjacency[previous_station].add(station)


def main(current_location, destination, number_of_stops=0):
    if current_location not in all_stations:
        raise ValueError("Current location is not a station")
    if destination not in all_stations:
        raise ValueError("Destination is not a station")
    if current_location == destination:
        return 0

    queue = deque([(current_location, 0)])
    visited = {current_location}

    while queue:
        station, stops = queue.popleft()
        for neighbor in adjacency.get(station, []):
            if neighbor in visited:
                continue
            if neighbor == destination:
                return number_of_stops + stops + 1
            visited.add(neighbor)
            queue.append((neighbor, stops + 1))

    raise ValueError(f"No route found from {current_location} to {destination}")


if __name__ == "__main__":
    result = main("Craigieburn", "Pakenham")
    print(result)
