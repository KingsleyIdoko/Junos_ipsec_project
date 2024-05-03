from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.zones import ensure_list, get_zone_names
from utiliites_scripts.pool_data import is_valid_ipv4_address, is_valid_name, select_zone
from utiliites_scripts.address_book import address_book,map_subnets_to_zones,select_address_book
from utiliites_scripts.commit import run_pyez_tasks
script_dir = os.path.dirname(os.path.realpath(__file__))

class AddressBookManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def nat_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get address book")
            print("2. Create address book")
            print("3. Update address book")
            print("4. Delete address book")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                result, zone_names = self.get_address_book()
                print(result)
                print(zone_names)
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

    def get_address_book(self, get_addresses=False):
        response = self.nr.run(task=pyez_get_config, database=self.database)
        for nat in response:
            result = response[nat].result['configuration']
            try:
                zones = result['security']['zones']['security-zone']
                zones = ensure_list(zones)
                zone_names = get_zone_names(zones)
            except KeyError:
                print("Zones do not exist: Please create zones")
                return None
            hostname = result.get('system', {}).get('host-name') or \
                    result.get('groups', [{}])[0].get('system', {}).get('host-name', 'Unknown')

            print(f"Fetching address books or network objects from {hostname} device")

            addresses = result.get('security', {}).get('address-book')
            if get_addresses:
                return addresses
            if addresses:
                return addresses, zone_names
            else:
                print(f"Address books or network objects are empty on {hostname} device.")
                print("Please create at least one network object.")
                return None

    def create_address_book(self):
            addresses, zone =  self.get_address_book()
            try:
                existing_addressbook = map_subnets_to_zones(addresses)
                addressbook_name, zone_selected = select_address_book(existing_addressbook)
            except:
                addressbook_name = None
                zone_selected = select_zone(zone)
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
            payload  = address_book(addressbook_name, address_name, ipv4_address, zone_selected)
            return payload
    
    def update_address_book(self):
        print("updating address book")
        
    def delete_address_book(self):
        print("Delete address book")
    def push_config(self):
        pass

    def push_config(self, operation=None):  
        if operation == "nat_operations":
            xml_data = self.nat_operations()
        else:
            return None
        if not xml_data:
            return None
        return run_pyez_tasks(self, xml_data, 'xml')
    

class AddressBookService:
    def __init__(self):
        self.address_book_manager = AddressBookManager()

    def use_get_address_book(self):
        result, zone_names = self.address_book_manager.get_address_book()
        return result, zone_names

if __name__ == "__main__":
    manager = AddressBookManager()
    manager.push_config(operation="nat_operations")