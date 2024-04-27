from utiliites_scripts.commons import get_valid_selection, get_valid_name
from sec_addressbook import AddressBookManager
from sec_zone import SecurityZoneManager
zone_manager = SecurityZoneManager()
address_manager = AddressBookManager()

def create_policy(from_zone, to_zone, name, source, destination, vpn, pair):
                    policy = f"""<policy>
                        <from-zone-name>{from_zone}</from-zone-name>
                        <to-zone-name>{to_zone}</to-zone-name>
                        <policy>
                            <name>{name}</name>
                            <match>
                                <source-address>{source}</source-address>
                                <destination-address>{destination}</destination-address>
                                <application>any</application>
                            </match>
                            <then>
                                <permit>
                                    <tunnel>
                                        <ipsec-vpn>{vpn}</ipsec-vpn>
                                        <pair-policy>{pair}</pair-policy>
                                    </tunnel>
                                </permit>
                            </then>
                        </policy>
                    </policy>"""
                    return policy

def gen_sec_policies_config(**kwargs):
    raw_data = kwargs.get('raw_data')
    if not raw_data:
        print("No raw data provided. grabbing existing zones")
        zone_names  = zone_manager.get_security_zone(get_zone_name=True)
    policy_data = extract_policy_names(raw_data)
    list_zones = list(policy_data.keys())
    if not list_zones:
        print("No zones available.")
        return None
    choice = get_valid_selection("Please select the security zone: ", list_zones)
    if choice:
        selected_policies = policy_data.get(choice, [])
        print("This following polices already exist, Please create new policy")
        for i, policy in enumerate(selected_policies, start=1):
            print(f'{i}. {policy}') 
        sec_policy_name = get_valid_name("Enter security policy name: ")
        _, from_zone, to_zone = choice.split('_to_')
        src_address = get_valid_selection("Select source address: " src_address)
        dest_address = get_valid_selection("Select destination address: ", dst_address)
        application = get_valid_selection("Select application to allow: ", applications)
        action = get_valid_selection("Selection match action: ", ["permit","deny"])
        ipsec_vpn = " "
        pair_policy = ""



def extract_policy_names(data):
    policies_by_zone = {}
    if data:
        for entry in data:
            from_zone = entry['from-zone-name']
            to_zone = entry['to-zone-name']
            zone_key = f"zone_{from_zone}_to_{to_zone}"
            policies_by_zone.setdefault(zone_key, [])
            for policy in entry['policy']:  
                policy_name = policy['name']
                policies_by_zone[zone_key].append(policy_name)
    return policies_by_zone if data else None