import textwrap

def nat_policy(global_nat_rule, source_zone, destination_zone, rule_name, remote_prefixes, source_prefixes=[None], nat_type=None):
    # Initialize an empty list to store the destination addresses
    prefixes = []
    for type_nat, value in nat_type.items():
        if type_nat == 'off':
            source_nat = f"""<source-nat><off/></source-nat>"""
        
        elif type_nat == 'interface':
            source_nat = f"""<source-nat><interface></interface></source-nat>"""      
        else:
            source_nat = f"""<source-nat><interface></interface></source-nat>"""  

    if source_prefixes !=  [None]:
        if len(source_prefixes) > 1:
            for src_prefix in source_prefixes:
                # Append the destination address element with the prefix value
                prefixes.append(f"<source-address>{src_prefix}</source-address>")
        else:
            prefixes.append(f"<source-address>{source_prefixes[0]}</source-address>")

    # Loop through the nat exempt vpn prefixes

    for dst_prefix in remote_prefixes:
        # Append the destination address element with the prefix value
        prefixes.append(f"<destination-address>{dst_prefix}</destination-address>")
    # except:
    #         prefixes.append(f"<destination-address>{remote_prefixes}</destination-address>")

    # Join the destination address elements with proper indentation
    prefixes = textwrap.indent('\n'.join(prefixes),'')

    # Create the payload with the f-string and the variable values
    payload = f"""
                <configuration>
                <security>
                    <nat>
                        <source>
                            <rule-set>
                            <name>{global_nat_rule}</name>
                            <from><zone>{source_zone}</zone></from>
                            <to><zone>{destination_zone}</zone></to>
                            <rule>
                            <name>{rule_name}</name>
                            <src-nat-rule-match>{prefixes}</src-nat-rule-match>
                            <then>{source_nat}</then>
                            </rule>
                            </rule-set>
                        </source>
                    </nat>
                </security>
                </configuration>
            """
    # Return the payload
    return payload

def delete_default_rules():
    payload = f"""
            <configuration>
                <security>
                    <nat operation="delete"/>
                </security>
            </configuration>"""
    return payload



def update_rule_names(rule_list):
    # Check if the list is already sorted in ascending order
    if all(x <= y for x, y in zip(rule_list, rule_list[1:])):
        # Return the list as it is
        return rule_list
    else:
        # Create an empty list
        items_list = []
        # Loop through the rule_list
        for items in rule_list:
            # Append the rule names to the items_list
            items_list.append(items[0])
        
        # Sort the items_list in ascending order
        items_list = sorted(items_list)
        
        # Loop through the rule_list and the items_list
        for data, item in zip(rule_list, items_list):
            # Update the rule names in the rule_list
            data[0] = item
        
        # Return the updated rule_list
        return rule_list