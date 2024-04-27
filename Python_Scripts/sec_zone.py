from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.security_zones import (select_zone, update_zone,zone_interface_names,find_available_interfaces,
                                     list_zone, extract_zone_names, delete_sec_zone)
from utiliites_scripts.interfaces import get_interfaces
from utiliites_scripts.commit import run_pyez_tasks
from sec_addressbook import AddressBookService

script_dir = os.path.dirname(os.path.realpath(__file__))

class SecurityZoneManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def nat_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Security Zones")
            print("2. Create Security Zone")
            print("3. Update Security Zone")
            print("4. Delete Security Zone")
            operation = input("Enter your choice (1-4): ")

            if operation == "1":
                return self.get_security_zone(interactive=True)
            elif operation == "2":
                return self.create_security_zone()
            elif operation == "3":
                return self.update_security_zone()
            elif operation == "4":
                return self.delete_security_zone()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_security_zone(self, interactive=False,get_zone_name=False):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            for zones in response:
                sec_zones = response[zones].result['configuration']['security']['zones']['security-zone']
                zone_names = [zone_name['name'] for zone_name in sec_zones if sec_zones]
                used_interfaces = zone_interface_names(sec_zones)
                interfaces = response[zones].result['configuration']['interfaces']
                All_intefaces = get_interfaces(interfaces)
                Unsed_interfaces = find_available_interfaces(All_intefaces, used_interfaces)
            if interactive:
                print(sec_zones)
                return 
            if get_zone_name:
                return zone_names
            return zones, Unsed_interfaces
        except Exception as e:
            print(f"An error has occurred: {e}")
            print(f"Pleaes check connectivity to the device")
            return None
        
    def create_security_zone(self):
        zones,interface_list = self.get_security_zone()
        print(interface_list)
        print("See existing zones below.......\n")
        zone_names = [zone['name'] for zone in zones]
        payload = select_zone(zone_names, interface_list)
        return payload
    
    def update_security_zone(self):
        zones, interface_list = self.get_security_zone()
        payload = update_zone(zones, interface_list)
        return payload
    
    def delete_security_zone(self):
        address_book = AddressBookService()
        addressbook, zone_names = address_book.use_get_address_book()
        zone  = list_zone(zone_names)
        used_zones = extract_zone_names(addressbook)
        if zone not in used_zones:
           payload =  delete_sec_zone(zone)
           return payload
        else:
            print(f"{zone} is in use or associated with the network object below:")

    def push_config(self):
        xml_data = self.nat_operations()
        if not xml_data:
            return None
        run_pyez_tasks(self, xml_data, 'xml') 
        
if __name__ == "__main__":
    config = SecurityZoneManager()
    response = config.push_config()