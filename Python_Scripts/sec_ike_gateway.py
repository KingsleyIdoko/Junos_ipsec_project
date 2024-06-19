
from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os, sys
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.gateways import gen_ikegateway_config, gen_ike_gateway_config, del_ike_gateway
from sec_basemanager import BaseManager
from utiliites_scripts.main_func import main

script_dir = os.path.dirname(os.path.realpath(__file__))

class IkeGatewayManager(BaseManager):
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Ike gateways")
            print("2. Create Ike gateway")
            print("3. Update Ike gateway")
            print("4. Delete Ike gateway")
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

    def get(self, interactive=False, get_raw_data=False, used_policy=False, target=None):
        try:
            response = self.nr.filter(name=target).run(task=pyez_get_config, database=self.database)
            if response.failed:
                print("Failed to connect to the device.")
                return None
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
            print(f"An error has occurred: {e}. Failed to retrieve gateways due to connectivity issues.")
            return None


    def create(self, target):
        try:
            old_gateways = self.get_ike_gateways(target=target)
            if not old_gateways:
                old_gateways = []  
            payload = gen_ikegateway_config(old_gateways=old_gateways)
            return payload
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


    def update(self, target):
        from sec_ipsec_vpn import IpsecVpnManager
        vpn_manager = IpsecVpnManager()
        get_gateways = vpn_manager.get_ipsec_vpn(get_used_gateways=True)
        used_ike_gateways = get_gateways if get_gateways else []
        try:
            ike_gateways = self.get_ike_gateways(get_raw_data=True, target=target)
            if ike_gateways:
                return gen_ike_gateway_config(ike_gateways=ike_gateways, used_ike_gateways=used_ike_gateways)
        except Exception as e:
            print(f"No existing IKE gateways found on the device. Error: {e}")


    def delete(self, target, commit=False, gateway_name=None, get_used_gateways=None):
        from sec_ipsec_vpn import IpsecVpnManager
        vpn_manager = IpsecVpnManager()
        if not get_used_gateways:
            get_used_gateways = vpn_manager.get_ipsec_vpn(get_used_gateways=True)
        if not gateway_name:
            gateway_name = self.get_ike_gateways(target=target)
        if not commit:
            payload = del_ike_gateway(gateway_names=gateway_name, get_used_gateways=get_used_gateways)
            return payload
        else:
            payload = del_ike_gateway(gateway_names=gateway_name, get_used_gateways=get_used_gateways)
            run_pyez_tasks(self, payload, 'xml')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ike_gateway_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, IkeGatewayManager)
