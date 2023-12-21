import textwrap

def nat_policy(global_nat_rule, source_zone, destination_zone, rule_set, nat_exempt_vpn_prefixes):

    # Initialize an empty list to store the destination addresses
    prefixes = []

    # Loop through the nat exempt vpn prefixes
    for prefix in nat_exempt_vpn_prefixes:
        # Append the destination address element with the prefix value
        prefixes.append(f"<destination-address>{prefix}</destination-address>")

    # Join the destination address elements with proper indentation
    prefixes = textwrap.indent('\n'.join(prefixes),'')

    # Create the payload with the f-string and the variable values
    payload = f""" <configuration>
                        <security>
                            <nat>
                                <source>
                                    <rule-set>
                                        <name>{global_nat_rule}</name>
                                        <from>
                                            <zone>{source_zone}</zone>
                                        </from>
                                        <to>
                                            <zone>{destination_zone}</zone>
                                        </to>
                                        <rule>
                                            <name>{rule_set}</name>
                                            <src-nat-rule-match>
                                            {prefixes}
                                            </src-nat-rule-match>
                                            <then>
                                                <source-nat>
                                                    <off/>
                                                </source-nat>
                                            </then> 
                                        </rule>            
                                    </rule-set>     
                                </source>           
                            </nat>                  
                        </security>                 
                    </configuration>"""
    # Return the payload
    return payload



