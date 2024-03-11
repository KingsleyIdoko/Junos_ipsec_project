
import re
import ipaddress

def create_nat_pool(hostname, remote_subnet):
    if hostname == "LA-DC-SRX-FW-PRY":
          pool_name = "LA-NYC-POOL-NAT"
          pool_prefix = remote_subnet[1].get('ip-prefix')
    elif hostname == "NYC-DC-SRX-FW":
            pool_name = "NYC-LA-POOL-NAT"
            pool_prefix = remote_subnet[1].get('ip-prefix')
    else:
         return None
    payload = f""" <configuration>
                <security>
                    <nat>
                        <source>
                            <pool>
                                <name>{pool_name}</name>
                                <address>
                                    <name>{pool_prefix}</name>
                                </address>
                            </pool>
                        </source>
                    </nat>
                </security>
        </configuration>"""
    print(payload)
    return payload

def get_pool_data(nat_data):
    list_pool_names = []
    pool_name = nat_data.get('name')
    pool_address = nat_data['address'].get('name')
    if pool_name is None:
        return None
    elif isinstance(pool_name, list) and isinstance(pool_name, list):
            for pol_name, address_name in zip(pool_name, pool_address):
                payload = f"""
                    <configuration>
                            <security>
                                <nat>
                                    <source>
                                        <pool>
                                            <name>{pol_name}</name>
                                            <address>S
                                                <name>{address_name}</name>
                                            </address>
                                        </pool>
                                    </source>
                                </nat>
                            </security>
                    </configuration>"""
                list_pool_names.append(payload)
            return list_pool_names
    else:
        payload = f"""
        <configuration>
                <security>
                    <nat>
                        <source>
                            <pool>
                                <name>{pool_name}</name>
                                <address>
                                    <name>{pool_address}</name>
                                </address>
                            </pool>
                        </source>
                    </nat>
                </security>
        </configuration>"""
        return payload


def nat_pool_creation(pool_name, pool_prefix):
    payload = f""" <configuration>
                <security>
                    <nat>
                        <source>
                            <pool>
                                <name>{pool_name}</name>
                                <address>
                                    <name>{pool_prefix}</name>
                                </address>
                            </pool>
                        </source>
                    </nat>
                </security>
        </configuration>"""
    return payload

def delete_nat_pool(name):
    payload = f"""
    <configuration>
            <security>
                <nat>
                    <source>
                        <pool operation="delete">
                            <name>{name}</name>
                        </pool>
                    </source>
                </nat>
            </security>
    </configuration>"""
    return payload


def check_nat_pull_duplicates(data, nat_pool_name, address_name):
    # Ensure data is in list format even if it's a single dictionary
    if isinstance(data, dict):
        data = [data]
    
    for pool in data:
        # Check if nat_pool_name matches the pool's name
        if nat_pool_name == pool['name']:
            result = "Name already exist in the pool"
            return result
        # Check if address_name matches the address's name within the pool
        if 'address' in pool and address_name == pool['address'].get('name'):
            result = "Prefix already exist in the pool"
            return result
    return False


def is_valid_nat_pool_name(name):
    # Regular expression to match names with A-Z, a-z, and _
    return bool(re.match(r'^[A-Za-z_]+$', name))

def is_valid_ipv4_address(address):
    try:
        # This will validate whether the input is a valid IPv4 address or subnet
        ipaddress.ip_network(address, strict=False)
        return True
    except ValueError:
        return False


def extract_pool_names(config):
    pool_names = []
    # Iterate over each rule in the config['rule']
    for rule in config.get('rule', []):
        # Extract pool-name if present in the 'then' part of the rule
        if 'pool' in rule.get('then', {}).get('source-nat', {}):
            pool_name = rule['then']['source-nat']['pool'].get('pool-name')
            if pool_name:
                pool_names.append(pool_name)
    
    return pool_names
