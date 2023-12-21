def create_policy(from_zone, to_zone, name, source, destination, vpn, pair):
                    policy = f"""<policy>
                        <from-zone-name>{from_zone}</from-zone-name>
                        <to-zone-name>{to_zone}</to-zone-name>
                        <policy>
                            <name>{name}</name>
                            <match>
                                <source-address>{source}</source-address>
                                <destination-address>{destination}</destination-address>
                                <application>any</application>
                            </match>
                            <then>
                                <permit>
                                    <tunnel>
                                        <ipsec-vpn>{vpn}</ipsec-vpn>
                                        <pair-policy>{pair}</pair-policy>
                                    </tunnel>
                                </permit>
                            </then>
                        </policy>
                    </policy>"""
                    return policy


