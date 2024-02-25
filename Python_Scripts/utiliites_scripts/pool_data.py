
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



