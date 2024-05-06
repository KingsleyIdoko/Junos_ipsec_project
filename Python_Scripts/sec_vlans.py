from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import time
import os
from utiliites_scripts.vlans import gen_vlan_config
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.commons import get_valid_string, get_valid_integer
from utiliites_scripts.vlans import extract_vlan_members, gen_delete_vlan_config, match_vlan_id
from sec_basemanager import BaseManager
script_dir = os.path.dirname(os.path.realpath(__file__))

class VlansManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Vlans")
            print("2. Create Vlan")
            print("3. Update Vlan")
            print("4. Delete Vlan")  
            try:
                operation = int(input("Enter your choice (1-4): "))
                if 1 <= operation <= 4:
                    if operation == 1:
                        return self.get_vlans(interactive=True)
                    elif operation == 2:
                        return self.create_vlan()
                    elif operation == 3:
                        return self.update_vlan()
                    elif operation == 4:
                        return self.delete_vlan()
                    break 
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Invalid input. Please enter an integer.")

    def get_vlans(self, interactive=False, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    for vlans in response:
                        vlan = response[vlans].result['configuration']['vlans']
                        vlan_members = response[vlans].result['configuration']['interfaces']
                        if interactive:
                            print(vlan['vlan'])
                        return vlan, vlan_members
            except Exception as e:
                print(f"An error has occurred: {e}")
                print("Check connectivity to the device, trying again...")
            attempt += 1
        print("Failed to retrieve interfaces after several attempts.")
        return None


    def create_vlan(self, vlan_id=None, vlan_name=None, commit_directly = False):
        print("Creating VLAN.......\n")
        retry_limit = 3
        attempts = 0
        while attempts < retry_limit:
            try:
                existing_vlans, *_ = self.get_vlans()
                vlan_ids = [vlan['vlan-id'] for vlan in existing_vlans['vlan']]
                break  
            except ValueError as e:
                print(f"An error occurred: {e}. Checking connectivity to device...")
                time.sleep(10)
                attempts += 1
        if attempts == retry_limit:
            print("Failed to connect to the device after several attempts.")
            return None
        if not vlan_id:
            vlan_id = get_valid_integer("Please enter a valid VLAN num (1-4094): ")
        if str(vlan_id) in vlan_ids:
            print(f"VLAN {vlan_id} already exists. Try again.")
            return None  
        if not vlan_name:
            vlan_name = get_valid_string("Enter VLAN name: ")
        payload = gen_vlan_config(vlan_id, vlan_name)
        print(f"VLAN {vlan_id} created successfully.")
        print(payload)
        if not commit_directly:
            return payload
        else:
            run_pyez_tasks(self, payload, 'xml')


    def update_vlan(self):
        print("Updating VLAN.............\n")
        attempts = 0
        max_attempts = 5
        while True:
            if attempts >= max_attempts:
                print("Maximum attempts reached. Exiting...")
                break
            try:
                existing_vlans, *_ = self.get_vlans()
                if existing_vlans is None:
                    print("No VLANs found. Exiting...")
                    break
                vlan_update_id = str(get_valid_integer("Enter VLAN-ID to update: "))
                new_vlan_name = get_valid_string("Enter new VLAN name: ")
                found_vlan = False
                payload = []
                for vlan in existing_vlans['vlan']:
                    if vlan['vlan-id'] == vlan_update_id:
                        vlan['name'] = new_vlan_name
                        payload.append(self.delete_vlan(choice=vlan_update_id, check_used=False))
                        response = gen_vlan_config(vlan['vlan-id'], vlan['name'])
                        found_vlan = True
                        print(f"VLAN {vlan_update_id} updated successfully.")
                        payload.append(response)
                        return payload  
                if not found_vlan:
                    print("VLAN does not exist on the device.")
                    choice = get_valid_string("Do you want to create a new VLAN (yes/no)? ").lower()
                    if choice == "yes":
                        print(f"Creating {new_vlan_name} with VLAN-ID {vlan_update_id}.")
                        payload = gen_vlan_config(vlan_update_id, new_vlan_name)
                        return payload
                    else:
                        print("No VLAN created or updated. Exiting...")
                        break
            except ValueError as e:
                print("Checking connectivity to the device")
                print(f"Error occurred: {e}")
                time.sleep(5)
                attempts += 1  
                continue  


    def delete_vlan(self, choice=None, check_used=True):
        print("Deleting VLAN...")
        existing_vlans, vlan_members = self.get_vlans()
        used_vlans, int_name = extract_vlan_members(vlan_members)  
        while True:
            if not choice:
                choice = get_valid_integer("Enter VLAN-ID to delete: ")
            if check_used and str(choice) in used_vlans:
                print(f"VLAN {choice} is in use. First, remove it from the interface {int_name}.")
                break  
            matched_vlan_name = match_vlan_id(str(choice), existing_vlans)
            if matched_vlan_name:
                payload = gen_delete_vlan_config(matched_vlan_name)
                print(f"VLAN {choice} deleted successfully.")
                return payload 
            else:
                print("No VLAN found with that ID.")
                break  

if __name__ == "__main__":
    config = VlansManager()
    response = config.push_config()