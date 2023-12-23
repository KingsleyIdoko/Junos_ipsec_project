def append_nat_data(result, remote_subnets):
    # Initialize an empty list for the sub nat rules
    sub_nat_rules = []
    # Initialize an empty list for the nat exempt vpn prefixes
    nat_exempt_vpn_prefixes = []

    nat_data = []
    
    # Loop through the remote subnets and append the ip prefixes to the list

    for subnet in remote_subnets:
        nat_exempt_vpn_prefixes.append(subnet['ip-prefix'])
    
    # Append the name, from zone, and to zone to the nat data list
    nat_data.append(result['name'])
    nat_data.append(result['from']['zone'])
    nat_data.append(result['to']['zone'])

    list_of_rules = result['rule']
    try:
        for nat_rule in list_of_rules:
            sub_nat_rules.append(nat_rule.get('name'))
    except:
        sub_nat_rules.append(list_of_rules.get('name'))
        
    nat_rule_name = "rule" + str(len(sub_nat_rules) + 1)
    
    # Append the nat rule name and the nat exempt vpn prefixes to the nat data list
    nat_data.append(nat_rule_name)
    nat_data.append(nat_exempt_vpn_prefixes)
    
    # Return the updated nat data list
    print(nat_data)
    return nat_data
