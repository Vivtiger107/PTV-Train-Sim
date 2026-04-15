import json
import random
import time
from datetime import datetime, timedelta
import os

with open("stations_routes.json", "r") as f:
    raw_stations_data = json.load(f)
    metro_services = raw_stations_data["M"]
    metro_tunnel_services = raw_stations_data["MT"]
    v_line_services = raw_stations_data["V"]
    all_services = metro_services | metro_tunnel_services | v_line_services
    all_stations = set()
    stations_services = {}
    for provider in raw_stations_data:
        for service in raw_stations_data[provider]:
            for direction in raw_stations_data[provider][service]:
                for station in direction:
                    if station not in stations_services.keys():
                        stations_services[station] = set()
                    all_stations.add(station)
                    stations_services[station].add(service)

with open("routes_time.json", "r") as f:
    routes_times = json.load(f)
    new_routes_times = {}
    for route_time in routes_times.items():
        new_routes_times[route_time[0]] = route_time[1] / len(all_services[route_time[0]][0])
    routes_times = new_routes_times

with open("save.json", "r") as f:
    save_data = json.load(f)
    points = save_data["Points"]
    clock = datetime.fromisoformat(save_data["Time"])
    current_location = save_data["Current location"]
    mission = tuple(save_data["Mission"])

print("Welcome to the train game, this is a representation of the victorian train system. Enjoy!")

def main():
    global current_location, points
    print(f"Available services from {current_location} are:")
    for service in stations_services[current_location]:
        print(service)
    change_station_to_town_hall = "N"
    change_station_to_state_library = "N"
    change_station_to_flinders_street = "N"
    change_station_to_melbourne_central = "N"
    if current_location == "Flinders Street":
        change_station_to_town_hall = input("Do you want to go to town hall, to change to the metro tunnel(Y/N)? ").upper()
    if current_location == "Melbourne Central":
        change_station_to_state_library = input("Do you want to go to state library, to change to the metro tunnel(Y/N)? ").upper()
    if current_location == "Town Hall":
        change_station_to_flinders_street = input("Do you want to go to flinders street to access services outside of the metro tunnel(Y/N)? ").upper()
    if current_location == "State Library":
        change_station_to_melbourne_central = input("Do you want to go to melbourne central to access services outside of metro tunnel(Y/N)? ").upper()
    if change_station_to_town_hall == "Y":
        current_location = "Town Hall"
        main()
    if change_station_to_flinders_street == "Y":
        current_location = "Flinders Street"
        main()
    if change_station_to_melbourne_central == "Y":
        current_location = "Melbourne Central"
        main()
    if change_station_to_state_library == "Y":
        current_location = "State Library"
        main()
    if not mission[0]:
        set_mission(current_location)
    print(f"Your mission is to go to {mission[0]}")
    want_to_quit = input("Press ENTER to see the timetable and type QUIT to leave the game or write CLUE to get a clue for the mission (Costs 5 points for a clue). ").upper()
    if want_to_quit == "QUIT":
        save()
    if want_to_quit == "CLUE":
        if points >= 5:
            points -= 5
            print(f"5 points deducted, points balance is now {points}")
            print(f"Clue: {stations_services[mission[0]]} go to {mission[0]}")
        else:
            print("You do not have enough points for a clue. Sorry")
    timetable = None
    see_more_timetable = "Y"
    refresh = True
    while see_more_timetable == "Y":
        if refresh:
            if timetable:
                timetable = create_timetable(current_location, timetable["time"])
            else:
                timetable = create_timetable(current_location, 0)
            time_index = 0
            for service_time in timetable["timetable"]:
                print(f"{time_index} {service_time}: {timetable["timetable_times"][time_index]}")
                time_index += 1
        see_more_timetable = input("Would you like to see more timetables? (Y or number of train you want): ").upper().strip()
        if see_more_timetable != "Y":
            refresh = False
            if not see_more_timetable.isdigit():
                print("Please type a number or a proper yes (Y)")
                see_more_timetable = "Y"
            else:
                try:
                    train = int(see_more_timetable)
                    current_train = timetable["timetable"][train]
                    time_for_train = timetable["timetable_times"][train]
                except:
                    print("Please type a number or a proper yes (Y)")
                    see_more_timetable = "Y"
    print("Waiting for train...")
    wait(time_for_train)
    print(f"Mission: {mission[0]}")
    print("You have boarded the train")
    os.system("say 'Train is now ready to depart, please stand clear of the platform'")
    direction = (1 if "to city" in current_train else 0)
    leave = "N"
    while leave != "Y":
        current_location = train_line(current_location, direction, current_train.replace(" to city", ""))
        if all_services[current_train.replace(" to city", "")][direction].index(current_location) == 0:
            leave = "Y"
        if all_services[current_train.replace(" to city", "")][direction].index(current_location) == len(all_services[current_train.replace(" to city", "")][direction]) - 1:
            leave = "Y"
        if leave != "Y":
            leave = input("Would you like to leave at this station? (Y/N): ").upper()
            if leave == "Y" and current_train.replace(" to city", "") in v_line_services:
                if direction == 0:
                    metro_stations = set()
                    for service in raw_stations_data["M"]:
                        for station in raw_stations_data["M"][service][1]:
                            metro_stations.add(station)
                    if current_location in metro_stations:
                        print("Sorry, you cannot leave at this station, Vline only allows outbound trains to stop at regional stations")
                        leave = "N"
        else:
            print("This train terminates here. All change please")
            os.system("say 'This train terminates here. All change please'")
        if leave == "Y":
            if check_mission(current_location):
                print("Mission achieved!")
                print(f"Points: {points}")
                os.system("say 'Mission achieved!'")
                os.system("afplay 'Level complete.wav'")
    main()

def create_timetable(current_location, time):
    services = stations_services[current_location]
    start_allowed = services.copy()
    end_allowed = services.copy()
    for service in services:
        try:
            if all_services[service][0].index(current_location) == 0:
                start_allowed.remove(service)
        except ValueError:
            pass
        try:
            if all_services[service][0].index(current_location) == (len(all_services[service][0]) - 1):
                end_allowed.remove(service)
        except ValueError:
            pass
        metro_stations = set()
        for service_ in raw_stations_data["M"]:
            for station_ in raw_stations_data["M"][service_][1]:
                metro_stations.add(station_)
        if service in raw_stations_data["V"] and current_location in metro_stations:
            try:
                start_allowed.remove(service)
            except ValueError:
                continue
    timetable = []
    timetable_times = []
    time = time
    for _ in (range(len(start_allowed)) if start_allowed > end_allowed else range(len(end_allowed))):
        if start_allowed:
            timetable.append(random.choice(list(start_allowed)) + " to city")
            time = random.randint(time, time + rush_hour_check())
            timetable_times.append(time)
        if end_allowed:
            timetable.append(random.choice(list(end_allowed)))
            time = random.randint(time, time + rush_hour_check())
            timetable_times.append(time)
    return {"timetable": timetable, "timetable_times": timetable_times, "time": time}


def train_line(current_location, direction, service):
    if direction == 0:
        if service in ("Bairnsdale", "Pakenham", "Cranbourne", "Frankston", "Sandringham", "Glen Waverley", "Alamein", "Belgrave", "Lilydale"):
            via = "Richmond"
        elif service in ("Hurstbridge", "Mernda"):
            via = "Jolimont"
        elif service in ("Craigeburn", "Upfield", "Werribee", "Williamstown"):
            via = "North Melbourne"
        elif service == "Sunbury":
            via = "State Library"
        elif service in ("Cranbourne", "East Pakenham"):
            via = "Anzac"
        else:
            via = "Southern Cross"
    if direction == 1:
        via = "The City Loop"
    if direction == 0:
        ending_station = service
    if direction == 1 and service in [service_ for service_ in metro_services]:
        ending_station = "Flinders Street"
    if direction == 1 and service in [service_ for service_ in metro_tunnel_services]:
        ending_station = "Town Hall"
    if direction == 1 and service in [service_ for service_ in v_line_services]:
        ending_station = "Southern Cross"
    os.system(f"say 'This is a service to {ending_station}, stopping all stations via {via}'")
    if direction == 1:
        try:
            current_location_index = all_services[service][direction].index(current_location)
        except ValueError:
            direction = 0 if direction == 1 else 1
            current_location_index = all_services[service][direction].index(current_location)
        if current_location_index != len(all_services[service][direction]) - 1:
            wait(routes_times[service])
            print(f"Points: {points}")
            print(f"Mission: {mission[0]}")
            while True:
                current_location = all_services[service][direction][current_location_index + 1]
                if 12 < clock.hour <= 16:
                    if current_location in ("Flagstaff", "Melbourne Central", "Parliament"):
                        current_location_index += 1
                        continue
                    break
                break
            location_services = stations_services[current_location].copy()
            location_services.remove(service)
            if location_services:
                print(f"Now at {current_location}, change here for {location_services}")
                os.system(f"say 'Now at {current_location}, change here for {location_services} services'")
            else:
                print(f"Now at {current_location}")
                os.system(f"say 'Now at {current_location}'")
        else:
            print("You are already in the city: Error 001")
    else:
        try:
            current_location_index = all_services[service][direction].index(current_location)
        except ValueError:
            direction = 0 if direction == 1 else 1
            current_location_index = all_services[service][direction].index(current_location)
        if current_location_index != len(all_services[service][direction]) - 1:
            wait(routes_times[service])
            print(f"Points: {points}")
            print(f"Mission: {mission[0]}")
            current_location = all_services[service][direction][current_location_index + 1]
            location_services = stations_services[current_location].copy()
            location_services.remove(service)
            if location_services:
                print(f"Now at {current_location}, change here for {location_services}")
                os.system(f"say 'Now at {current_location}, change here for {location_services} services'")
            else:
                print(f"Now at {current_location}")
                os.system(f"say 'Now at {current_location}'")
        else:
            print(f"You are already at {service} which is the end of the line: Error 002")
    return current_location

def show_time():
    global clock
    print("\n"*50)
    print(clock.strftime("%d/%m/%Y %I:%M:%S %p"))

def wait(minutes):
    global clock
    time.sleep(minutes)
    clock += timedelta(minutes=minutes)
    show_time()

def set_mission(current_location):
    global mission
    mission = current_location
    while mission == current_location:
        mission = (random.choice(list(all_stations)), False)

def achieve_mission():
    global mission, points
    points += random.randint(1, 5)
    mission = random.choice(list(all_stations)), False
    return mission

def check_mission(current_location):
    if current_location == mission[0]:
        return achieve_mission()
    else:
        return False

def save():
    with open("save.json", "w") as f:
        save_data = {"Points": points, "Time": clock.isoformat(), "Current location": current_location, "Mission": list(mission)}
        json.dump(save_data, f)
    exit()

def rush_hour_check():
    global clock
    hour = clock.hour
    if hour <= 4:
        return 60
    elif hour <= 8:
        return 5
    elif hour <= 12:
        return 5
    elif hour <= 16:
        return 5
    elif hour <= 20:
        return 15
    elif hour <= 24:
        return 30
    else:
        print("Error happened in checking time for timetable, error handled: Error 003")
        return 5

if __name__ == "__main__":
    show_time()
    main()
