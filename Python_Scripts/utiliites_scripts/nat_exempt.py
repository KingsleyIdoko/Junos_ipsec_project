import textwrap

def nat_policy(global_nat_rule, source_zone, destination_zone, rule_name, remote_prefixes, source_prefixes, nat_type):
    # Initialize an empty list to store the destination addresses
    prefixes = []

    nat_type = []

    source_nat_int = f"""
                    <source-nat>
                        <interface>
                        </interface>
                    </source-nat>"""
    
    source_nat_off = f"""
                    <source-nat>
                        <off/>
                    </source-nat>"""
    
    if nat_type == 'interface':
        source_nat_prefix = f"""
                        <source-nat>
                            <interface>
                            </interface>
                        </source-nat>"""      
            
    elif nat_type == 'off':
        source_nat_prefix = f"""
                        <source-nat>
                            <off/>
                        </source-nat>"""       
        # Loop through the nat exempt vpn prefixes
    for src_prefix in source_prefixes:
        # Append the destination address element with the prefix value
        prefixes.append(f"<source-address>{src_prefix}</source-address>")
         

    # Loop through the nat exempt vpn prefixes
    for dst_prefix in remote_prefixes:
        # Append the destination address element with the prefix value
        prefixes.append(f"<destination-address>{dst_prefix}</destination-address>")

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
                                            <name>{rule_name}</name>
                                            <src-nat-rule-match>
                                            {prefixes}
                                            </src-nat-rule-match>
                                            <then>
                                                {nat_type}
                                            </then> 
                                        </rule>            
                                    </rule-set>     
                                </source>           
                            </nat>                  
                        </security>                 
                    </configuration>"""
    # Return the payload
    return payload



