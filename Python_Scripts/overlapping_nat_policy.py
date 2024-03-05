from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.fetch_data import append_nat_data
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.selectprefix import select_prefix, select_nat_type
script_dir = os.path.dirname(os.path.realpath(__file__))

class NatPolicy:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def fetch_nat_data(self):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in response:
                result = response[nat].result['configuration']['security']['nat']['source']['rule-set']
                remote_subnets =  response[nat].result['configuration']['security']['address-book'][1]['address']
                source_subnets =  response[nat].result['configuration']['security']['address-book'][0]['address']
                nat_pool = response[nat].result['configuration']['security']['nat']['source']['pool']
                pool_name = response[nat].result['configuration']['security']['nat']['source']['pool'].get('name')
                try:
                    hostname = response[nat].result['configuration']['system']['host-name']
                except: 
                    hostname = response[nat].result['configuration']['groups'][0]['system']['host-name']
                if hostname == "NYC-DC-SRX-FW":
                    print("Select Remote Prefixes............\n")
                    remote_subnets = select_prefix(remote_subnets)
                    print("Select Source Prefixes............\n")
                    source_subnets = select_prefix(source_subnets)
                elif hostname == "LA-DC-SRX-FW-PRY":
                    print("Select Remote Prefixes............\n")
                    remote_subnets = select_prefix(remote_subnets)
                    print("Select Source Prefixes............\n")
                    source_subnets = select_prefix(source_subnets)
                nat_data = append_nat_data(result, hostname, remote_subnets, source_subnets)
            return nat_data, pool_name
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
        
    def overlapping_subnet(self):
        xml_data = []
        dictionaries = [{'off': None}, {'pool': None}, {'interface': None}]
        nat_type = select_nat_type(dictionaries)
        nat_data, pool_name = self.fetch_nat_data()
        global_nat_rule, source_zone, destination_zone, rule_name, remote_prefixes, source_prefixes = nat_data
        payload = minidom.parseString(nat_policy( global_nat_rule, source_zone, destination_zone, rule_name, nat_type, remote_prefixes, source_prefixes, pool_name))
        formatted_xml = payload.toprettyxml()
        formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
        return formatted_xml
    
    def push_config(self):
        new_nat_policy = self.overlapping_subnet()
        run_pyez_tasks(self, new_nat_policy, 'xml') 
        
config = NatPolicy()
result = config.push_config()