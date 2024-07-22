import requests
import configparser
import csv
import pandas as pd


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
TARGET_LEVEL = 100 # The level to get weapon stats for
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

    # Clean up weapons CSV
    clear_empty_columns(WEAPON_DATA_FILE)
    postprocess_columns(WEAPON_DATA_FILE)


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
            writer.writerow(prune_nonTargetLevel(flatten_base_stats(weapon, stats_map)))


# Flatten a dict that contains base stats into just a raw dict
def flatten_base_stats(weapon, stats_map):
    BASE_STAT = 'base_stat'
    STAT_ID = 'stat_id'
    STAT_VALUE = 'stat_value'

    flattened_stats = {}

    for key, value in weapon.items():
        if key != BASE_STAT:
            flattened_stats[key] = value
    
    if BASE_STAT in weapon:
        for stat in weapon[BASE_STAT]:
            stat_id = stat.get(STAT_ID)
            stat_value = stat.get(STAT_VALUE)
            if (stat_id is not None and stat_value is not None):
                stat_name = stats_map.get(stat_id)
                if (stat_name is not None):     
                    flattened_stats[stat_name] = stat_value
                elif (DEBUG):
                    print(f"Stat with stat ID {stat_id} and stat value {stat_value} not found for weapon {weapon['weapon_name']}")   
    
    return flattened_stats


# Acquire target level stats for all guns for gun attack
def prune_nonTargetLevel(weapon, stats_map={}):
    FIREARM_ATK = 'firearm_atk'
    LEVEL = 'level'

    pruned_stats = {}
    for key, value in weapon.items():
        if key != FIREARM_ATK:
            pruned_stats[key] = value
    
    if FIREARM_ATK in weapon:
        for item in weapon[FIREARM_ATK]:
            if item['level'] == TARGET_LEVEL:
                pruned_stats[FIREARM_ATK] = item['firearm'][0]['firearm_atk_value']
    
    return pruned_stats


# Clear empty columns
def clear_empty_columns(file):
    df = pd.read_csv(file)
    df_cleaned = df.dropna(axis=1, how='all')
    df_cleaned.to_csv(file, index=False)


# Order columns and drop some miscellany
def postprocess_columns(file):
    df = pd.read_csv(file)

    # Drop image columns and weapon ID
    df = df.drop(columns=['image_url', 'weapon_perk_ability_image_url', 'weapon_id'])

    # Define the order of columns
    starting_columns = [
        'weapon_name',
        'weapon_tier',
        'weapon_type',
        'weapon_rounds_type',
        "firearm_atk"
    ]
    
    ending_columns = [
        'weapon_perk_ability_name',
        'weapon_perk_ability_description'
    ]

    remaining_columns = [col for col in df.columns if col not in starting_columns and col not in ending_columns]
    remaining_columns.sort()

    final_columns = starting_columns + remaining_columns + ending_columns

    df = df[final_columns]
    df.to_csv(file, index=False)


if __name__ == '__main__':
    main()