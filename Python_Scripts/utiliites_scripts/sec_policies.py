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


def config_data(self, local_policy, local_subnet, tunnel_name, remote_policy, remote_subnet):
    trust_untrust = create_policy(
        from_zone="trust",
        to_zone="untrust",
        name=local_policy,
        source=local_subnet,
        destination=remote_subnet,
        vpn=tunnel_name,
        pair=remote_policy,
    )
    untrust_trust = create_policy(
        from_zone="untrust",
        to_zone="trust",
        name=remote_policy,
        source=remote_subnet,
        destination=local_subnet,
        vpn=tunnel_name,
        pair=local_policy,
    )
    payload = f"""
    <configuration>
        <security>
            <policies>
                {trust_untrust}
                {untrust_trust}
            </policies>
        </security>
    </configuration>"""
    return payload