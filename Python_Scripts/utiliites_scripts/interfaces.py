def get_interfaces(device_interfaces):
    interface_names = []

    for interface in device_interfaces['interface']:
        # Exclude interfaces starting with 'fab' and 'fxp'
        if interface['name'].startswith('fab') or interface['name'].startswith('fxp'):
            continue

        # Check if 'gigether-options' is present and prefer 'parent' if available
        gigether_options = interface.get('gigether-options')
        if gigether_options:
            parent = gigether_options.get('redundant-parent', {}).get('parent')
            if parent:
                interface_names.append(parent)
                continue  # Move to the next interface after adding the parent
        
        # Add the interface name if not processed above
        interface_names.append(interface['name'])

    # Remove duplicates to ensure the interfaces returned are unique
    return list(set(interface_names))
