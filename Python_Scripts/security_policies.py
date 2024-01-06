from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.sec_policies import config_data

# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

class DeviceConfigurator:
    database = 'committed'


    def __init__(self, config_file="config.yml"):
        # Initialize the Nornir object with the config file
        self.nr = InitNornir(config_file=config_file)

    def get_device_configs(self):
        try:
            self.response = self.nr.run(task=pyez_get_config, database=self.database)

            for _, value in self.response.items():
                try:
                    self.vpn_tunnel_names = value.result['configuration']['security']['ipsec']['vpn']['name']
                    self.security_policies = value.result['configuration']['security']['policies']['policy']
                    self.address_book =  value.result['configuration']['security']['address-book']
                    self.device_hostnames = value.result['configuration']['system']['host-name']
                except:
                    pass
                    tunnel_names = []
                    self.vpn_tunnel_names = value.result['configuration']['security']['ipsec']['vpn']
                    for vpn in self.vpn_tunnel_names:
                        tunnel_names.append(vpn['name'])
                    self.vpn_tunnel_names =  tunnel_names
                    self.security_policies = value.result['configuration']['security']['policies']['policy']
                    self.address_book =  value.result['configuration']['security']['address-book']
                    self.device_hostnames = value.result['configuration']['groups'][0]['system']['host-name']
            return self.vpn_tunnel_names, self.security_policies, self.device_hostnames, self.address_book
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None, None, None  # Return None for all lists in case of an error  

    def get_policy_names(self):
        _, response, *args = self.get_device_configs()
        trust_to_untrust = []
        untrust_to_trust = []
        for policy in response:
            from_zone = policy['from-zone-name']
            to_zone = policy['to-zone-name']
            for p in policy['policy']:
                policy_name = p['name']
                if from_zone == 'trust' and to_zone == 'untrust':
                    trust_to_untrust.append(policy_name)
                elif from_zone == 'untrust' and to_zone == 'trust':
                    untrust_to_trust.append(policy_name)
        trust_to_untrust = [policy for policy in trust_to_untrust if policy != 'default_trust_untrust']
        untrust_to_trust = [policy for policy in untrust_to_trust if policy != 'default_untrust_trust']
        return trust_to_untrust, untrust_to_trust
    
    def get_address_book(self):
        *args, hostname, address_book = self.get_device_configs()
        local_subnet_names = []
        remote_subnet_names = []
        for entry in address_book:
            book_name = entry['name']
            if 'address' in entry and isinstance(entry['address'], list):
                book_values = [item['name'] for item in entry['address']]
            elif 'address' in entry and isinstance(entry['address'], dict):
                book_values = [entry['address']['name']]
            else:
                book_values = []
            if book_name == 'local_subnets':
                local_subnet_names.extend(book_values)
            elif book_name == 'remote_subnet':
                remote_subnet_names.extend(book_values)    
        return local_subnet_names, remote_subnet_names

    def build_config(self):
        tunnel_name, _, hosts, _ = self.get_device_configs()
        local_subnet, remote_subnet = self.get_address_book()
        if hosts == "LA-DC-SRX-FW-PRY":
            local_policy = ['LA_NYC_POLICY','LA_AMS_POLICY','LA_BEL_POLICY']
            remote_policy = ['NYC_LA_POLICY','AMS_LA_POLICY','BEL_LA_POLICY']   
        elif hosts == "NYC-DC-SRX-FW":
            local_policy = ['NYC_LA_POLICY']
            remote_policy = ['LA_NYC_POLICY']
        elif hosts == "AMS-DC-SRX-FW":
            local_policy = ['AMS_LA_POLICY']
            remote_policy = ['LA_AMS_POLICY']

        # Initialize an empty list to store individual policy dictionaries
        if len(local_policy) and len(remote_policy) > 1:
            policies = []
            for local_policy, remote_policy, tunnel in zip(local_policy, remote_policy, tunnel_name):  
                if remote_policy == 'NYC_LA_POLICY':
                    local_sub = local_subnet[1]
                    remote_sub  = remote_subnet[2]
                elif remote_policy == 'AMS_LA_POLICY':
                    local_sub = local_subnet[0]
                    remote_sub  = remote_subnet[1]        
                elif remote_policy == 'BEL_LA_POLICY':
                    local_sub = local_subnet[0]
                    remote_sub = remote_subnet[0]   
                policy = config_data(local_policy, local_sub, tunnel, remote_policy, remote_sub)
                policies.append(policy)
        else:
            policy = config_data(local_policy[0], local_subnet, tunnel_name, remote_policy[0], remote_subnet)
            policies = policy
        print(policies[0])
        return policies

    def push_config(self):
        _, _, hostname, _ = self.get_device_configs()
        xml_data = self.build_config()
        print(xml_data)
        if hostname == "LA-DC-SRX-FW-PRY":
            for index in range(len(xml_data)):
                response = self.nr.run(task=pyez_config, payload=xml_data[index], data_format='xml')
                diff_result = self.nr.run(task=pyez_diff)
                for res in diff_result:
                    if diff_result[res].result == None:
                        print("No Config Change")
                    else:
                        print(diff_result[res].result)
                        if diff_result:
                            committed = self.nr.run(task=pyez_commit)
                            for res1 in committed:
                                print(committed[res1].result)
        else:
            response = self.nr.run(task=pyez_config, payload=xml_data, data_format='xml')
            if response:
                diff_result = self.nr.run(task=pyez_diff)
                for res in diff_result:
                    if diff_result[res].result == None:
                        print("No Config Change")
                    else:
                        print(diff_result[res].result)
                        if diff_result:
                            committed = self.nr.run(task=pyez_commit)
                            for res1 in committed:
                                print(committed[res1].result)

config = DeviceConfigurator(config_file=f"{script_dir}/config.yml")
response = config.push_config()
