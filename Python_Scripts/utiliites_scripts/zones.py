def ensure_list(input_item):
    if isinstance(input_item, dict):
        # If it's a dictionary, wrap it in a list
        return [input_item]
    elif isinstance(input_item, list):
        # If it's already a list, return it as is
        return input_item
    else:
        # Handle other data types if necessary, e.g., raise an error
        raise TypeError("Expected a dictionary or a list of dictionaries")
    
def get_zone_names(zones_data):
    normalized_zones = ensure_list(zones_data)
    zone_names = [zone['name'] for zone in normalized_zones]
    return zone_names
