from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.security_zones import select_zone, update_zone, zone_interface_names,find_available_interfaces
from utiliites_scripts.interfaces import get_interfaces
from utiliites_scripts.commit import run_pyez_tasks

script_dir = os.path.dirname(os.path.realpath(__file__))

class SecurityZoneManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def nat_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. GET Security Zones")
            print("2. Create Security Zone")
            print("3. Update Security Zone")
            print("4. Delete Security Zone")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                result = self.get_security_zone()
                return result
            elif operation == "2":
                result = self.create_security_zone()
                return result
            elif operation == "3":
                 result = self.update_security_zone()
                 return result
            elif operation == "4":
                return self.delete_security_zone()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_security_zone(self):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            for zones in response:
                result = response[zones].result['configuration']['security']['zones']['security-zone']
                used_interfaces = zone_interface_names(result)
                interfaces = response[zones].result['configuration']['interfaces']
                All_intefaces = get_interfaces(interfaces)
                Unsed_interfaces = find_available_interfaces(All_intefaces, used_interfaces)
                try:
                    hostname = response[zones].result['configuration']['system']['host-name']
                except: 
                    hostname = response[zones].result['configuration']['groups'][0]['system']['host-name']
            return result, hostname, Unsed_interfaces
        except Exception as e:
            print(f"An error has occurred: {e}")
            print(f"Device checking connectivity")
            return None
        
    def create_security_zone(self):
        zones, hostname, interface_list = self.get_security_zone()
        print("See existing zones below.......\n")
        zone_names = [zone['name'] for zone in zones]
        payload = select_zone(zone_names, interface_list)
        return payload
    
    def update_security_zone(self):
        zones, *_, interface_list = self.get_security_zone()
        payload = update_zone(zones, interface_list)
        return payload
    
    def delete_security_zone(self):
        pass

    def push_config(self):
        xml_data = self.nat_operations()
        if not xml_data:
            return None
        run_pyez_tasks(self, xml_data, 'xml') 

config = SecurityZoneManager()
response = config.push_config()