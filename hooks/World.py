import random

# Object classes from AP core, to represent an entire MultiWorld and this individual World that's part of it
from worlds.AutoWorld import World
from BaseClasses import MultiWorld, CollectionState

# Object classes from Manual -- extending AP core -- representing items and locations that are used in generation
from ..Items import ManualItem
from ..Locations import ManualLocation

# Raw JSON data from the Manual apworld, respectively:
#          data/game.json, data/items.json, data/locations.json, data/regions.json
#
from ..Data import game_table, item_table, location_table, region_table

# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value

# calling logging.info("message") anywhere below in this file will output the message to both console and log file
import logging

########################################################################################
## Order of method calls when the world generates:
##    1. create_regions - Creates regions and locations
##    2. create_items - Creates the item pool
##    3. set_rules - Creates rules for accessing regions and locations
##    4. generate_basic - Runs any post item pool options, like place item/category
##    5. pre_fill - Creates the victory location
##
## The create_item method is used by plando and start_inventory settings to create an item from an item name.
## The fill_slot_data method will be used to send data to the Manual client for later use, like deathlink.
########################################################################################



random.seed()
countryside_tiles = random.sample(range(1, 12), k=7)
random.shuffle(countryside_tiles)
core_non_city_tiles = random.sample(range(1, 5), k=2)
core_city_tiles = random.sample(range(5, 9), k=2)
core_tiles = core_non_city_tiles + core_city_tiles
random.shuffle(core_tiles)
map_tiles = countryside_tiles + core_tiles
countryside_tiles_with_ruins = [tile for tile in countryside_tiles if tile in [8, 10, 11]]
core_tiles_with_ruins = [tile for tile in core_tiles if tile in [2, 3, 4, 8]]
tiles_with_ruins = countryside_tiles_with_ruins + core_tiles_with_ruins
ruins_tiles = random.sample(range(1, 13), k=len(tiles_with_ruins))
ruins_tiles = [tile if tile < 9 else tile + 2 for tile in ruins_tiles]  # Why do the tile numbers skip 9 and 10 <_<
random.shuffle(ruins_tiles)

ruins_tiles_logic = {1: {"item": "2 Artifacts", "required_level_ups": 4},
                     2: {"item": "Artifact + Advanced Action", "required_level_ups": 4},
                     3: {"item": "Artifact + Spell", "required_level_ups": 4},
                     4: {"item": "Artifact", "required_level_ups": 2},
                     5: {"item": "Recruit a Unit", "required_level_ups": 2},
                     6: {"item": "Artifact", "required_level_ups": 1},
                     7: {"item": "4 Mana Crystals", "required_level_ups": 1},
                     8: {"item": "Spell + 4 Mana Crystals", "required_level_ups": 2},
                     11: {"item": "+7 Fame", "required_level_ups": 0},
                     12: {"item": "+7 Fame", "required_level_ups": 0},
                     13: {"item": "+7 Fame", "required_level_ups": 0},
                     14: {"item": "+7 Fame", "required_level_ups": 0},
}


# Use this function to change the valid filler items to be created to replace item links or starting items.
# Default value is the `filler_item_name` from game.json
def hook_get_filler_item_name(world: World, multiworld: MultiWorld, player: int) -> str | bool:
    return False

# Called before regions and locations are created. Not clear why you'd want this, but it's here. Victory location is included, but Victory event is not placed yet.
def before_create_regions(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after regions and locations are created, in case you want to see or modify that information. Victory location is included.
def after_create_regions(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to remove locations from the world
    locationNamesToRemove = [] # List of location names


    # Add your code here to calculate which locations to remove
    # Remove the random map tiles which aren't being used
    for region in multiworld.regions:
        if region.name.startswith("Countryside") or region.name.startswith("Core"):
            region_name_split = region.name.split()
            tile_type = region_name_split[0]
            tile_number = int(region_name_split[2])

            if tile_type == "Countryside":
                if tile_number not in countryside_tiles:
                    for location in list(region.locations):
                        locationNamesToRemove.append(location.name)
                else:
                    tiles_required = countryside_tiles.index(tile_number) + 1
                    region.entrances[0].access_rule = lambda state: state.has("Map Tile", player, tiles_required)
            elif tile_type == "Core":
                if tile_number not in core_tiles:
                    for location in list(region.locations):
                        locationNamesToRemove.append(location.name)
                else:
                    tiles_required = core_tiles.index(tile_number) + 8  # Need all 7 countryside tiles before collecting any core tiles
                    region.entrances[0].access_rule = lambda state: state.has("Map Tile", player, tiles_required)
                    for location in list(region.locations):
                        location.access_rule = lambda state: location.access_rule(state) and region.entrances[0].access_rule(state)


    for region in multiworld.regions:
        if region.player == player:
            for location in list(region.locations):
                if location.name in locationNamesToRemove:
                    region.locations.remove(location)
    if hasattr(multiworld, "clear_location_cache"):
        multiworld.clear_location_cache()

# The item pool before starting items are processed, in case you want to see the raw item pool at that stage
def before_create_items_starting(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

# The item pool after starting items are processed but before filler is added, in case you want to see the raw item pool at that stage
def before_create_items_filler(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    # Use this hook to remove items from the item pool
    itemNamesToRemove = [] # List of item names

    # Add your code here to calculate which items to remove.
    #
    # Because multiple copies of an item can exist, you need to add an item name
    # to the list multiple times if you want to remove multiple copies of it.


    # Removing the items for each map tile that isn't being used
    if 1 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
    if 2 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
    if 3 not in countryside_tiles:
        itemNamesToRemove.append("Keep - Increased Hand Limit")
    if 4 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
        itemNamesToRemove.append("Spell")
    if 5 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
        itemNamesToRemove.append("Artifact")
    if 6 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
        itemNamesToRemove.append("2 Mana Crystals")
    if 7 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
        itemNamesToRemove.append("Artifact")
        itemNamesToRemove.append("Spell/Artifact")
    if 8 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
        itemNamesToRemove.append("Ruins Reward")
    if 9 not in countryside_tiles:
        itemNamesToRemove.append("Keep - Increased Hand Limit")
        itemNamesToRemove.append("Spell")
        itemNamesToRemove.append("Spell/Artifact")
    if 10 not in countryside_tiles:
        itemNamesToRemove.append("Keep - Increased Hand Limit")
        itemNamesToRemove.append("Ruins Reward")
        itemNamesToRemove.append("2 Mana Crystals")
    if 11 not in countryside_tiles:
        itemNamesToRemove.append("+1 Reputation")
        itemNamesToRemove.append("Spell")
        itemNamesToRemove.append("Ruins Reward")

    if 1 not in core_tiles:
        itemNamesToRemove.append("Artifact")
        itemNamesToRemove.append("Artifact + 3 Mana Crystals")
        itemNamesToRemove.append("Spell + Artifact")
    if 2 not in core_tiles:
        itemNamesToRemove.append("Spell")
        itemNamesToRemove.append("Ruins Reward")
        itemNamesToRemove.append("+2 Reputation")
    if 3 not in core_tiles:
        itemNamesToRemove.append("Spell")
        itemNamesToRemove.append("Ruins Reward")
        itemNamesToRemove.append("Spell + Artifact")
    if 4 not in core_tiles:
        itemNamesToRemove.append("Keep - Increased Hand Limit")
        itemNamesToRemove.append("Ruins Reward")
        itemNamesToRemove.append("+2 Reputation")
    if 5 not in core_tiles:
        itemNamesToRemove.append("+1 Reputation")
        itemNamesToRemove.append("+1 Reputation")
    if 6 not in core_tiles:
        itemNamesToRemove.append("Artifact")
        itemNamesToRemove.append("+2 Reputation")
    if 7 not in core_tiles:
        itemNamesToRemove.append("Keep - Increased Hand Limit")
        itemNamesToRemove.append("Artifact + 3 Mana Crystals")
        itemNamesToRemove.append("+2 Reputation")
    if 8 not in core_tiles:
        itemNamesToRemove.append("Ruins Reward")
        itemNamesToRemove.append("+2 Reputation")
        itemNamesToRemove.append("+2 Reputation")

    for itemName in itemNamesToRemove:
        item = next(i for i in item_pool if i.name == itemName)
        item_pool.remove(item)

    ruins_count = 0
    for item in item_pool:
        if item.name == "Ruins Reward":
            item.name = ruins_tiles_logic[ruins_tiles[ruins_count]]["item"]
            ruins_count = ruins_count + 1

    return item_pool

    # Some other useful hook options:

    ## Place an item at a specific location
    # location = next(l for l in multiworld.get_unfilled_locations(player=player) if l.name == "Location Name")
    # item_to_place = next(i for i in item_pool if i.name == "Item Name")
    # location.place_locked_item(item_to_place)
    # item_pool.remove(item_to_place)

# The complete item pool prior to being set for generation is provided here, in case you want to make changes to it
def after_create_items(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

# Called before rules for accessing regions and locations are created. Not clear why you'd want this, but it's here.
def before_set_rules(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after rules for accessing regions and locations are created, in case you want to see or modify that information.
def after_set_rules(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to modify the access rules for a given location

    def Example_Rule(state: CollectionState) -> bool:
        # Calculated rules take a CollectionState object and return a boolean
        # True if the player can access the location
        # CollectionState is defined in BaseClasses
        return True

    ## Common functions:
    # location = world.get_location(location_name, player)
    # location.access_rule = Example_Rule

    ## Combine rules:
    # old_rule = location.access_rule
    # location.access_rule = lambda state: old_rule(state) and Example_Rule(state)
    # OR
    # location.access_rule = lambda state: old_rule(state) or Example_Rule(state)

    for region in multiworld.regions:
        if region.name.startswith("Countryside") or region.name.startswith("Core"):
            region_name_split = region.name.split()
            tile_type = region_name_split[0]
            tile_number = int(region_name_split[2])

            if tile_type == "Countryside" and tile_number in countryside_tiles:
                if tile_number > 7 and tile_number in tiles_with_ruins:
                    ruins_location_index = region.locations.index(region.name + " - Ruins")
                    ruins_tile = ruins_tiles[tiles_with_ruins.index(tile_number)]
                    region.locations[ruins_location_index].access_rule = lambda state: state.has("Level Up Bonuses", player, ruins_tiles_logic[ruins_tile]["required_level_ups"] * 2)
                tiles_required = countryside_tiles.index(tile_number) + 1
                region.entrances[0].access_rule = lambda state: state.has("Map Tile", player, tiles_required)
            elif tile_type == "Core" and tile_number in core_tiles:
                if tile_number in tiles_with_ruins:
                    ruins_location_index = region.locations.index(region.name + " - Ruins")
                    ruins_tile = ruins_tiles[tiles_with_ruins.index(tile_number)]
                    region.locations[ruins_location_index].access_rule = lambda state: state.has("Level Up Bonuses", player, ruins_tiles_logic[ruins_tile]["required_level_ups"] * 2)
                tiles_required = core_tiles.index(tile_number) + 8  # Need all 7 countryside tiles before collecting any core tiles
                region.entrances[0].access_rule = lambda state: state.has("Map Tile", player, tiles_required)

# The item name to create is provided before the item is created, in case you want to make changes to it
def before_create_item(item_name: str, world: World, multiworld: MultiWorld, player: int) -> str:
    return item_name

# The item that was created is provided after creation, in case you want to modify the item
def after_create_item(item: ManualItem, world: World, multiworld: MultiWorld, player: int) -> ManualItem:
    return item

# This method is run towards the end of pre-generation, before the place_item options have been handled and before AP generation occurs
def before_generate_basic(world: World, multiworld: MultiWorld, player: int) -> list:
    pass

# This method is run at the very end of pre-generation, once the place_item options have been handled and before AP generation occurs
def after_generate_basic(world: World, multiworld: MultiWorld, player: int):
    pass

# This is called before slot data is set and provides an empty dict ({}), in case you want to modify it before Manual does
def before_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called after slot data is set and provides the slot data at the time, in case you want to check and modify it after Manual is done with it
def after_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called right at the end, in case you want to write stuff to the spoiler log
def before_write_spoiler(world: World, multiworld: MultiWorld, spoiler_handle) -> None:
    pass

# This is called when you want to add information to the hint text
def before_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    
    ### Example way to use this hook: 
    # if player not in hint_data:
    #     hint_data.update({player: {}})
    # for location in multiworld.get_locations(player):
    #     if not location.address:
    #         continue
    #
    #     use this section to calculate the hint string
    #
    #     hint_data[player][location.address] = hint_string
    
    pass

def after_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    pass
