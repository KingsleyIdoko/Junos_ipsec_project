
from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os, logging
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.gateways import gen_ikegateway_config,extract_gateways_params, del_ike_gateway
script_dir = os.path.dirname(os.path.realpath(__file__))

class IkeGatewayManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def ike_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Ike gateways")
            print("2. Create Ike gateway")
            print("3. Update Ike gateway")
            print("4. Delete Ike gateway")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_ike_gateways(interactive=True)
            elif operation == "2":
                return self.create_ike_gateway()
            elif operation == "3":
                return self.update_ike_gateway()
            elif operation == "4":
                return  self.delete_ike_gateway()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ike_gateways(self, interactive=False, get_raw_data=False, used_policy=False, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response.failed:
                    print("Failed to connect to the device, trying again...")
                    attempt += 1
                    continue
                all_gateways = []
                all_policies = []
                for _, result in response.items():
                    ike_config = result.result.get('configuration', {}).get('security', {}).get('ike', {})
                    gateways = ike_config.get('gateway', [])
                    gateways = [gateways] if isinstance(gateways, dict) else gateways      
                    for gate in gateways:
                        if 'name' in gate:
                            all_gateways.append(gate['name'])
                        if 'ike-policy' in gate:
                            all_policies.append(gate['ike-policy'])    
                if not gateways:
                    print("No IKE Gateway configurations found on the device.")
                    return None
                if interactive:
                    print(gateways)
                    return
                if get_raw_data:
                    return gateways
                if used_policy:
                    return all_policies
                return all_gateways
            except Exception as e:
                print(f"An error has occurred: {e}. Checking connectivity to the device, trying again...")
                attempt += 1
        print("Failed to retrieve gateways after several attempts due to connectivity issues.")
        return None


    def create_ike_gateway(self):
        try:
            old_gateways = self.get_ike_gateways()
            if not old_gateways:
                print("No existing IKE Gateway found on the device")
                old_gateways = []  
            payload = gen_ikegateway_config(old_gateways=old_gateways)
            return payload
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def update_ike_gateway(self):
        from sec_ipsec_vpn import IpsecVpnManager
        vpn_manager = IpsecVpnManager()
        old_gateway_name = payload =  None
        used_ike_gateways = vpn_manager.get_ipsec_vpn(used_gateways=True)
        try:
            ike_gateways = self.get_ike_gateways(get_raw_data=True)
            if ike_gateways:
                payload, old_gateway_name = extract_gateways_params(ike_gateways=ike_gateways,used_ike_gateways=used_ike_gateways)
            if old_gateway_name:
                self.delete_ike_gateway(commit=True, gateway_name=old_gateway_name,used_ike_gateways=used_ike_gateways)
            return payload
        except Exception as e:
            print(f"An error occurred: {e}")
            print("No existing IKE gateways found on the device.")

    def delete_ike_gateway(self, commit=False, gateway_name=None):
        from sec_ipsec_vpn import IpsecVpnManager
        vpn_manager = IpsecVpnManager()
        used_gateways = vpn_manager.get_ipsec_vpn(used_gateways=True)
        if not commit:
            gateway_name = self.get_ike_gateways()
            payload = del_ike_gateway(gateway_name=gateway_name,used_gateways=used_gateways)
            return payload
        else:
            gateway_name=gateway_name
            payload = del_ike_gateway(gateway_name=gateway_name,used_gateways=used_gateways)
            run_pyez_tasks(self, payload, 'xml')

    def push_config(self):
        try:
            xml_data = self.ike_operations()
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
    config = IkeGatewayManager()
    response = config.push_config()