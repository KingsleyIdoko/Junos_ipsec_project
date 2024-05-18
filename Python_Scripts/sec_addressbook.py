from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os
from utiliites_scripts.zones import ensure_list, get_zone_names
from utiliites_scripts.address_book import gen_addressbook_config
from sec_basemanager import BaseManager
script_dir = os.path.dirname(os.path.realpath(__file__))


class AddressBookManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get address book")
            print("2. Create address book")
            print("3. Update address book")
            print("4. Delete address book")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_address_book(interactive=True)
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

    def get_address_book(self, get_addresses=False, interactive=False, get_address_book_by_name=False):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in response:
                result = response[nat].result['configuration']
                try:
                    zones = result['security']['zones']['security-zone']
                    zones = ensure_list(zones)
                    zone_names = get_zone_names(zones)
                except KeyError:
                    print("Zones do not exist: Please create zones.")
                    return None
                hostname = result.get('system', {}).get('host-name') or result.get('groups', [{}])[0].get('system', {}).get('host-name', 'Unknown')
                addresses = result.get('security', {}).get('address-book')
                if interactive:
                    if addresses:
                        print(addresses)
                    else:
                        print("Address book is empty on the device")
                    return None
                elif get_address_book_by_name:
                    if not isinstance(addresses, list):
                        addresses = [addresses]
                    address_book_names = [address.get('name') for address in addresses] if addresses else None
                    return address_book_names
                elif addresses:
                    return (addresses, None) if get_addresses else (addresses, zone_names)
                elif zone_names:
                    return None, zone_names
                else:
                    print(f"No address books or network objects found on {hostname} device.")
                    print("Please create at least one network object.")
                    return None, None
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None, None
        
    def create_address_book(self):
        addresses = zone = address_book_by_name = None
        try:
            addresses, zone = self.get_address_book()
        except Exception as e:
            print(f"An error occurred while fetching addresses and zones: {e}")
        try:
            address_book_by_name = self.get_address_book(get_address_book_by_name=True)
        except Exception as e:
            print(f"No address_book_by_name is present on the device")
        if addresses is None and zone is None:
            print("Failed to fetch addresses and zones. Cannot generate address book configuration.")
            return None
        try:
            payload = gen_addressbook_config(addresses, zone, address_book_by_name)
            if payload:
                print(payload)
            else:
                print("Failed to generate address book configuration.")
            return payload
        except Exception as e:
            print(f"An error occurred while generating address book configuration: {e}")
            return None


    def update_address_book(self):
        print("updating address book")
        
    def delete_address_book(self):
        print("Delete address book")

class AddressBookService:
    def __init__(self):
        self.address_book_manager = AddressBookManager()

    def use_get_address_book(self):
        result, zone_names = self.address_book_manager.get_address_book()
        return result, 

if __name__ == "__main__":
    config = AddressBookManager()
    response = config.push_config()
