from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.vlans import gen_vlan_config
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.commons import get_valid_string, get_valid_integer
from utiliites_scripts.vlans import extract_vlan_members, gen_delete_vlan_config, match_vlan_id



script_dir = os.path.dirname(os.path.realpath(__file__))

class VlansManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def vlans_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Vlans")
            print("2. Create Vlan")
            print("3. Update Vlan")
            print("4. Delete Vlan")  # Fixed the numbering here
            try:
                operation = int(input("Enter your choice (1-4): "))
                if 1 <= operation <= 4:
                    if operation == 1:
                        response =  self.get_vlans(interactive=True)
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


    def create_vlan(self):
        print("Creating vlan.......\n")
        while True:
            existin_vlans, *_ = self.get_vlans()
            vlan_ids = [vlan['vlan-id'] for vlan in existin_vlans['vlan']]
            vlan_id = get_valid_integer("Please enter a valid Vlan num (1-4094): ")
            vlan_name = get_valid_string("Enter vlan name: ")
            if vlan_id in vlan_ids:
                print(f"Vland {vlan_id} already exist, Try again")
            else:
                payload = gen_vlan_config(vlan_id, vlan_name)
                break
        return payload

    def update_vlan(self):
        """
        Updates the name of an existing VLAN or creates a new VLAN based on user input.
        """
        print("Updating VLAN.............\n")
        while True:
            existing_vlans, *_ = self.get_vlans()
            if existing_vlans is None:
                print("No VLANs found. Exiting...")
                break
            vlan_update_id = str(get_valid_integer("Enter VLAN-ID to update: "))
            new_vlan_name = get_valid_string("Enter new VLAN name: ")
            found_vlan = False
            for vlan in existing_vlans['vlan']:
                if vlan['vlan-id'] == vlan_update_id:
                    vlan['name'] = new_vlan_name
                    response = gen_vlan_config(vlan['vlan-id'], vlan['name'])
                    found_vlan = True
                    print(f"VLAN {vlan_update_id} updated successfully.")
                    return response
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


    # def delete_vlan(self, vlan_members):
    #     while True:
    #         existing_vlans, vlan_members = self.get_vlans()
    #         used_vlans, int_name = extract_vlan_members(vlan_members)
    #         choice = get_valid_integer("Enter VLAN-ID to find: ")
    #         if str(choice) in used_vlans:
    #             print("Vlan {choice} is in used. First remove it from interface {int_name}")
    #         else:
    #             matched_vlan_name = match_vlan_id(choice, existing_vlans)
    #             if matched_vlan_name:
    #                 payload = delete_vlan(matched_vlan_name)
    #                 return payload
    #             else:
    #                 print("No VLAN found with that ID.")



    def delete_vlan(self):
        print("Deleting VLAN...")
        while True:
            existing_vlans, vlan_members = self.get_vlans()
            used_vlans, int_name = extract_vlan_members(vlan_members)  # Assuming this returns a list of used VLAN IDs and optionally interface names
            choice = get_valid_integer("Enter VLAN-ID to delete: ")

            if str(choice) in used_vlans:
                print(f"VLAN {choice} is in use. First remove it from the interface {int_name}.")
                break
            else:
                matched_vlan_name = match_vlan_id(str(choice), existing_vlans)
                if matched_vlan_name:
                    payload = gen_delete_vlan_config(matched_vlan_name)
                    print(f"VLAN {choice} deleted successfully.")
                    return payload
                else:
                    print("No VLAN found with that ID.")
                    break
                

    def push_config(self):
        xml_data = self.vlans_operations()
        if not xml_data:
            return 
        elif isinstance(xml_data, list):
            for xml in xml_data:
                run_pyez_tasks(self, xml, 'xml') 
                return None
        else:
             run_pyez_tasks(self, xml_data, 'xml') 


config = VlansManager()
response = config.push_config()