
from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os, logging
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ipsec_proposal import gen_ipsec_proposal_config
script_dir = os.path.dirname(os.path.realpath(__file__))

class IPsecProposalManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def ipsec_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get IPsec Proposal")
            print("2. Create IPsec Proposal")
            print("3. Update IPsec Proposal")
            print("4. Delete Ipsec Prospoal")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_ipsec_proposal(interactive=True)
            elif operation == "2":
                return self.create_ipsec_proposal()
            elif operation == "3":
                return self.update_ipsec_proposal()
            elif operation == "4":
                return  self.delete_ipsec_proposal()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ipsec_proposal(self, interactive=False, get_raw_data=False, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response.failed:  
                    print("Failed to connect to the device, trying again...")
                    attempt += 1
                    continue
                for _, result in response.items():
                    ike_config = result.result['configuration']['security'].get('ipsec', {})
                    ipsec_proposal = ike_config.get('proposal', [])
                    ipsec_proposal = [ipsec_proposal] if isinstance(ipsec_proposal, dict) else ipsec_proposal
                    ipesec_ipsec_proposal = [ipsec_proposal['name'] for ipsec_proposal in ipsec_proposal if 'name' in ipsec_proposal]              
                if not ipsec_proposal:  
                    print("No IPsec Proposal configurations exist on the device.")
                    return None
                if interactive:
                    print(ipsec_proposal)
                    return
                if get_raw_data:
                    return ipsec_proposal
                return ipesec_ipsec_proposal
            except Exception as e:
                print(f"An error has occurred: {e}. Checking connectivity to the device, trying again...")
                attempt += 1
                continue  
        print("Failed to retrieve gateways after several attempts due to connectivity issues.")
        return None

    def create_ipsec_proposal(self):
        try:
            old_ipsec_proposal = self.get_ipsec_proposal()
            if not old_ipsec_proposal:
                print("No existing IPSEC Proposal found on the device")
            payload = gen_ipsec_proposal_config(old_ipsec_proposal=old_ipsec_proposal)
            print(payload)
            return payload
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def update_ipsec_proposal(self):
        pass
        # old_gateway_name = payload =  None
        # try:
        #     ike_gateways = self.get_ike_gateways(get_raw_data=True)
        #     if ike_gateways:
        #         payload, old_gateway_name = extract_gateways_params(ike_gateways=ike_gateways)
        #     if old_gateway_name:
        #         self.delete_ike_gateway(commit=True, gateway_name=old_gateway_name)
        #     return payload
        # except Exception as e:
        #     print(f"An error occurred: {e}")
        #     print("No existing IKE gateways found on the device.")

    def delete_ipsec_proposal(self, commit=False, gateway_name=None):
        pass
        # if not commit:
        #     gateway_name = self.get_ike_gateways()
        #     used_gateway = None
        #     payload = del_ike_gateway(gateway_name=gateway_name,used_gateway=used_gateway)
        #     return payload
        # else:
        #     gateway_name=gateway_name
        #     used_gateway = None
        #     payload = del_ike_gateway(gateway_name=gateway_name,used_gateway=used_gateway)
        #     run_pyez_tasks(self, payload, 'xml')

    def push_config(self):
        try:
            xml_data = self.ipsec_operations()
            if not xml_data:
                logging.info("No XML data to push.")
                return
            if isinstance(xml_data, list):
                for xml in xml_data:
                    try:
                        run_pyez_tasks(self, xml, 'xml')
                    except Exception as e:
                        logging.error(f"Failed to push configuration for {xml}: {e}")
            else:
                try:
                    run_pyez_tasks(self, xml_data, 'xml')
                except Exception as e:
                    logging.error(f"Failed to push configuration: {e}")
        except Exception as e:
            logging.error(f"Error in push_config: {e}")


if __name__ == "__main__":
    config = IPsecProposalManager()
    response = config.push_config()