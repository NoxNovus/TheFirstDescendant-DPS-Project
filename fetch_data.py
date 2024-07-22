import requests
import configparser
import json
import csv


## API CONSTANTS ##
config = configparser.ConfigParser()
config.read('config.ini')
api_key = config['API']['api_key']

HEADERS_DEFAULT = {
    "x-nxopen-api-key": api_key
}

LANGUAGE_MODIFIER = "/en" # for English results
TFD_API_URL_BASE = "https://open.api.nexon.com/static/tfd/meta" + LANGUAGE_MODIFIER

DESCENDANT = "/descendant.json"
WEAPON = "/weapon.json"
MODULE = "/module.json"
REACTOR = "/reactor.json"
EXTERNAL_COMPONENT = "/external-component.json"
REWARD = "/reward.json"
STAT = "/stat.json"
VOID_BATTLE = "/void-battle.json"
TITLE = "/title.json"


## LOCAL CONSTANTS ##
STAT_DATA_FILE = "weapon_stats.csv"
WEAPON_DATA_FILE = "weapon_data.csv"

DEBUG = True # Debug log messages?


def main():
    # Fetch stat data from API, and build a statID to statName dictionary, as well as writing data to CSV
    stats_raw = call_api(TFD_API_URL_BASE + STAT)
    stats_map = {stat['stat_id']: stat['stat_name'] for stat in stats_raw}
    
    # Add hardcoded missing stats too
    stats_map["105000132"] = "Mystery Stat" # What does this stat do?
    stats_map["105000200"] = "Burst Shot Delay"

    parse_stats(stats_map)

    # Fetch weapon data from API, and write data to CSV
    weapons_raw = call_api(TFD_API_URL_BASE + WEAPON)
    parse_weapons(weapons_raw, stats_map, WEAPON_DATA_FILE)


# Call the API and handle errors
def call_api(urlString, headers = HEADERS_DEFAULT):
    response = requests.get(urlString, headers = headers)
    assert (response.status_code == 200), f"Error fetching API, response was {response.json()}"
    return response.json()


# Parse through the stats data, writing to a csv
def parse_stats(stats_map):
    with open(STAT_DATA_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['stat_id', 'stat_name'])
        for stat_id, stat_name in stats_map.items():
            writer.writerow([stat_id, stat_name])


# Parse through the messy weapons data, writing to a csv
def parse_weapons(weapons_raw, stats_map, filename):
    # Fetch field names, append base_stat as well
    field_names = set(weapons_raw[0].keys())
    field_names.update(stats_map.values())

    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        for weapon in weapons_raw:
            writer.writerow(flatten_base_stats(weapon, stats_map))


# Flatten a dict that contains base stats into just a raw dict
def flatten_base_stats(weapon, stats_map):
    flattened_stats = {}
    
    if 'base_stat' in weapon:
        for stat in weapon['base_stat']:
            stat_id = stat.get('stat_id')
            stat_value = stat.get('stat_value')
            if (stat_id is not None and stat_value is not None):
                stat_name = stats_map.get(stat_id)
                if (stat_name is not None):     
                    flattened_stats[stat_name] = stat_value
                elif (DEBUG):
                    print(f"Stat with stat ID {stat_id} and stat value {stat_value} not found for weapon {weapon['weapon_name']}")   
    
    return flattened_stats

if __name__ == '__main__':
    main()