
from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ipsec_vpn import (gen_ipsec_vpn_config, update_ipsec_vpn,del_ipsec_vpn)
from sec_ipsec_policy import IpsecPolicyManager
from sec_ike_gateway import IkeGatewayManager
from sec_basemanager import BaseManager
vpn_manager = IpsecPolicyManager() 
gateway_manager = IkeGatewayManager()


class IpsecVpnManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        self.nr = super().__init__(config_file=config_file)
  
    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. get VPN policy")
            print("2. create VPN policy")
            print("3. update VPN policy")
            print("4. delete VPN policy")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_ipsec_vpn(interactive=True)
            elif operation == "2":
                return self.create_ipsec_vpn()
            elif operation == "3":
                return self.update_ipsec_vpn()
            elif operation == "4":
                return self.delete_ipsec_vpn()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ipsec_vpn(self,interactive=False,get_used_gateways=False,retries=3,get_vpn_name=False):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    raw_ipsec_vpn, ipsec_vpn_names, used_gateways = [], [], []
                    for _, result in response.items():
                        ipsec_config = result.result['configuration']['security'].get('ipsec', {})
                        if ipsec_config:
                            raw_ipsec_vpn = ipsec_config.get('vpn', [])
                            if isinstance(raw_ipsec_vpn, dict):
                                raw_ipsec_vpn = [raw_ipsec_vpn]
                            ipsec_vpn_names = [vpn['name'] for vpn in raw_ipsec_vpn if 'name' in vpn]
                            used_gateways.extend([vpn['ike']['gateway'] for vpn in raw_ipsec_vpn if "ike" in vpn and 'gateway' in vpn['ike']])
                        else:
                            print("No IPsec configuration found on the device.")
                            return None

                    if interactive:
                        print("Existing IPsec VPNs:", raw_ipsec_vpn if raw_ipsec_vpn else "No IPsec VPNs found.")
                        return None
                    if get_vpn_name:
                        return ipsec_vpn_names
                    if get_used_gateways:
                        return used_gateways
                    return raw_ipsec_vpn, ipsec_vpn_names if ipsec_vpn_names else None
            except Exception as e:
                print(f"An error has occurred: {e}. Trying again...")
            attempt += 1
        print("Failed to retrieve IPsec VPN configurations after several attempts.")
        return None

    def create_ipsec_vpn(self):
        old_ipsec_vpn = self.get_ipsec_vpn(get_vpn_name=True)
        ipsec_policy = vpn_manager.get_ipsec_policy(get_policy_name=True)
        ike_gateway =  gateway_manager.get_ike_gateways()
        print(ike_gateway)
        if not old_ipsec_vpn:
            print("No existing IPsec VPN found on the device")
        payload = gen_ipsec_vpn_config(old_ipsec_vpn=old_ipsec_vpn,ipsec_policy=ipsec_policy,
                                       ike_gateway=ike_gateway)
        return payload

    def update_ipsec_vpn(self):
        try:
            ipsec_vpns, old_vpn_names = self.get_ipsec_vpn()
            ike_gateway =  gateway_manager.get_ike_gateways()
            ipsec_policy = vpn_manager.get_ipsec_policy(get_policy_name=True)
            payload, del_vpn = update_ipsec_vpn(ipsec_vpns=ipsec_vpns, ike_gateway=ike_gateway,
                                        ipsec_policy=ipsec_policy,old_vpn_names=old_vpn_names)
            if del_vpn:
                self.delete_ipsec_vpn(commit=True, vpn_name=del_vpn)
            return payload
        except ValueError as e:
            print(f"An error has occured, {e}")
        
    def delete_ipsec_vpn(self, commit=False, vpn_name=None):
        if not commit:
            vpn_name = self.get_ipsec_vpn(get_vpn_name=True)
            used_policy = None
            payload = del_ipsec_vpn(vpn_name=vpn_name,used_policy=used_policy)
            return payload
        else:
            vpn_name=vpn_name
            used_policy = None
            payload = del_ipsec_vpn(vpn_name=vpn_name,used_policy=used_policy)
            run_pyez_tasks(self, payload, 'xml')


if __name__ == "__main__":
    config = IpsecVpnManager()
    response = config.push_config()