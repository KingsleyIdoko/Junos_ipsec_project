from nornir import InitNornir
from nornir_pyez.plugins.tasks import pyez_get_config, pyez_config
from nornir_utils.plugins.functions import print_result
from rich import print
import os, sys
from utiliites_scripts.main_func import main
from utiliites_scripts.commons import get_valid_selection
from utiliites_scripts.zones import ensure_list, get_zone_names
from utiliites_scripts.address_book import (
    gen_addressbook_config,
    gen_address_set_config,
    gen_updated_config,
    gen_delete_config
)
from sec_basemanager import BaseManager

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(os.path.join(script_dir, '..')))

class AddressBookManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)
        self.nr = InitNornir(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get address book")
            print("2. Create address book")
            print("3. Update address book")
            print("4. Delete address book")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return "get"
            elif operation == "2":
                return "create"
            elif operation == "3":
                return "update"
            elif operation == "4":
                return "delete"
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get(self, get_addresses=False, interactive=False, get_address_book_by_name=False, target=None):
        try:
            response = self.nr.filter(name=target).run(task=pyez_get_config, database=self.database)
            for nat in response:
                result = response[nat].result['configuration']
                try:
                    zones = result['security']['zones']['security-zone']
                    zones = ensure_list(zones)
                    zone_names = get_zone_names(zones)
                except KeyError:
                    print("Zones do not exist: Please create zones.")
                    return None, None
                hostname = result.get('system', {}).get('host-name') or result.get('groups', [{}])[0].get('system', {}).get('host-name', 'Unknown')
                addresses = result.get('security', {}).get('address-book')
                if interactive:
                    if addresses:
                        print(addresses)
                    else:
                        print("Address book is empty on the device")
                    return None, None
                elif get_address_book_by_name:
                    if addresses and not isinstance(addresses, list):
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
            print(f"could not retrieve configs from the device. Please check Connectivity. Error: {e}")
            return None, None

    def create(self, target):
        addresses = zone = address_book_by_name = None
        try:
            addresses, zone = self.get(target=target)
        except Exception as e:
            print(f"An error occurred while fetching addresses and zones: {e}")
        try:
            address_book_by_name = self.get(get_address_book_by_name=True, target=target)
        except Exception as e:
            print(f"No address_book_by_name is present on the device")
        if addresses is None and zone is None:
            print("Failed to fetch addresses and zones. Cannot generate address book configuration.")
            return None
        try:
            choice = get_valid_selection("Please select create operation:", ["create_address_book", "create address-set"])
            if choice == "create_address_book":
                payload = gen_addressbook_config(addresses, zone, address_book_by_name)
            else:
                payload = gen_address_set_config(addresses, zone, address_book_by_name)
            print(payload)
            return payload
        except Exception as e:
            print(f"An error occurred while generating address book configuration: {e}")
            return None

    def update(self, target):
        addresses = zone = address_book_by_name = None
        try:
            addresses, *_ = self.get(target=target)
        except Exception as e:
            print(f"An error occurred while fetching addresses and zones: {e}")
        try:
            address_book_by_name = self.get(get_address_book_by_name=True, target=target)
            return gen_updated_config(addresses, address_book_by_name)
        except Exception as e:
            print(f"No address_book_by_name is present on the device")
            return None

    def delete(self, target):
        addresses = zone = address_book_by_name = None
        try:
            addresses, *_ = self.get(target=target)
        except Exception as e:
            print(f"An error occurred while fetching addresses and zones: {e}")
        try:
            address_book_by_name = self.get(get_address_book_by_name=True, target=target)
            return gen_delete_config(addresses, address_book_by_name)
        except Exception as e:
            print(f"No address_book_by_name is present on the device")
            return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ike_gateway_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, AddressBookManager)