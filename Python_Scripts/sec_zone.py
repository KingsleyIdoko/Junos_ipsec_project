from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.security_zones import (
    select_zone, update_zone, zone_interface_names, find_available_interfaces,
    list_zone, extract_zone_names, delete_sec_zone
)
from utiliites_scripts.interfaces import get_interfaces
from sec_basemanager import BaseManager
from sec_addressbook import AddressBookManager
from utiliites_scripts.main_func import main

script_dir = os.path.dirname(os.path.realpath(__file__))

class SecurityZoneManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Security Zones")
            print("2. Create Security Zone")
            print("3. Update Security Zone")
            print("4. Delete Security Zone")
            try:
                operation = int(input("Enter your choice (1-4): "))
                if 1 <= operation <= 4:
                    if operation == 1:
                        return "get"
                    elif operation == 2:
                        return "create"
                    elif operation == 3:
                        return "update"
                    elif operation == 4:
                        return "delete"
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Invalid input. Please enter an integer.")

    def get(self, interactive=False, get_zone_name=False, target=None):
        try:
            response = self.nr.filter(name=target).run(task=pyez_get_config, database=self.database)
            for zones in response:
                sec_zones = response[zones].result['configuration']['security']['zones']['security-zone']
                zone_names = [zone_name['name'] for zone_name in sec_zones if sec_zones]
                used_interfaces = zone_interface_names(sec_zones)
                interfaces = response[zones].result['configuration']['interfaces']
                all_interfaces = get_interfaces(interfaces)
                unused_interfaces = find_available_interfaces(all_interfaces, used_interfaces)
            if interactive:
                print(sec_zones)
                return 
            if get_zone_name:
                return zone_names
            return sec_zones, unused_interfaces
        except Exception as e:
            print(f"An error has occurred: {e}")
            print(f"Please check connectivity to the device")
            return None

    def create(self, target):
        zones, interface_list = self.get(target=target)
        print("See existing zones below.......\n")
        zone_names = [zone['name'] for zone in zones]
        payload = select_zone(zone_names, interface_list)
        return payload

    def update(self, target):
        zones, interface_list = self.get(target=target)
        payload = update_zone(zones, interface_list)
        return payload

    def delete(self, target):
        address_book = AddressBookManager()
        addressbook, zone_names = address_book.use_get_address_book()
        zone = list_zone(zone_names)
        used_zones = extract_zone_names(addressbook)
        if zone not in used_zones:
           payload = delete_sec_zone(zone)
           return payload
        else:
            print(f"{zone} is in use or associated with the network object below:")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python security_zone_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, SecurityZoneManager)
