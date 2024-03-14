from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.zones import ensure_list, get_zone_names
from utiliites_scripts.pool_data import is_valid_ipv4_address, is_valid_name, select_zone
from utiliites_scripts.address_book import create_address_book,map_subnets_to_zones,select_address_book
from utiliites_scripts.commit import run_pyez_tasks
script_dir = os.path.dirname(os.path.realpath(__file__))

class AddressBookManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def nat_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. get address book")
            print("2. Create address book")
            print("3. Update address book")
            print("4. Delete address book")
            operation = input("Enter your choice (1-4): ")

            if operation == "1":
                result = self.get_address_book()
                return result
            elif operation == "2":
                result = self.create_address_book()
                return result
            elif operation == "3":
                return self.update_address_book()
            elif operation == "4":
                return self.delete_address_book()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue
    def get_address_book(self):
        response = self.nr.run(task=pyez_get_config, database=self.database)
        for nat in response:
            try:
                zones = response[nat].result['configuration']['security']['zones']['security-zone']
                zone = ensure_list(zones)
                zones = get_zone_names(zone)
            except:
                print("Zones does not exist: Please create zones")
            try:
                hostname = response[nat].result['configuration']['system']['host-name']
            except: 
                hostname = response[nat].result['configuration']['groups'][0]['system']['host-name']
            try:
                print(f"Fetching address books or network objects from {hostname} device")
                addresses = response[nat].result['configuration']['security'].get('address-book')
                return addresses, zones
            except:
                print(f"Address books or network objects is empty on {hostname} device")
                print(f"Please create at least one network object")
                self.create_address_book()     
                addresses = self.get_address_book() 
                return addresses
            
    def create_address_book(self):
            try:
                addresses, zone =  self.get_address_book()
                existing_addressbook = map_subnets_to_zones(addresses)
                addressbook_name = select_address_book(existing_addressbook)
            except:
                addressbook_name = None
            if addressbook_name is None:
                addressbook_name = input("specify address_name: ")
                while True:
                    if is_valid_name(addressbook_name):
                        break
                    else:
                        print("Name is not valid. Please enter a valid name.")
            while True:
                address_name = input("Specify name of prefix: ")
                if is_valid_name(address_name):
                    break
                else:
                    print("Name is not valid. Please enter a valid name.")
            while True:
                ipv4_address = input("Specify IPv4 address: ")
                if is_valid_ipv4_address(ipv4_address):
                    break
                else:
                    print("IPv4 address is not valid. Please enter a valid IPv4 address.")
            zone_selected = select_zone(zone)
            payload  = create_address_book(addressbook_name, address_name, ipv4_address, zone_selected)
            return payload

    def update_address_book(self):
        print("updating address book")
    def delete_address_book(self):
        print("Delete address book")
    def push_config(self):
        pass

    def push_config(self):  
        xml_data = self.nat_operations()
        print(xml_data)
        if not xml_data:
            return None
        run_pyez_tasks(self, xml_data, 'xml') 

config = AddressBookManager()
response = config.push_config()