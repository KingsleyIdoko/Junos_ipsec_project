def append_nat_data(result, hostname, remote_subnets, source_subnet):
    sub_nat_rules = []
    nat_exempt_vpn_prefixes = []
    src_subnet = []
    nat_data = []
    try:
        for subnet in remote_subnets:
            nat_exempt_vpn_prefixes.append(subnet['ip-prefix'])
    except:
            nat_exempt_vpn_prefixes.append(remote_subnets['ip-prefix'])
    try:
        for src_network in source_subnet:
            src_subnet.append(src_network['ip-prefix'])
    except:
        src_subnet.append(source_subnet.get('ip-prefix'))
    nat_data.append(result['name'])
    nat_data.append(result['from']['zone'])
    nat_data.append(result['to']['zone'])
    list_of_rules = result.get('rule')
    if list_of_rules:
        try:
            sub_nat_rules.append(list_of_rules.get('name'))
        except:
            for rule_names in list_of_rules:
                sub_nat_rules.append(rule_names.get('name'))
        rule_number = len(sub_nat_rules) + 1
        nat_rule_name = "rule" + str(rule_number)
        rule_number  = 1
        while nat_rule_name in sub_nat_rules:
                nat_rule_name = "rule" + str(rule_number)
                rule_number += 1
        new_nat_names =  nat_rule_name
    else:
        new_nat_names = "rule1"
    nat_data.append(new_nat_names)
    nat_data.append(nat_exempt_vpn_prefixes)
    nat_data.append(src_subnet)
    
    # Return the updated nat data list
    return nat_data


def Serialize_nat_data(nat_data):
    result = []
    try:
        name = nat_data.get('name')
        dst = [nat_data['src-nat-rule-match'].get('destination-address')]
        if len (dst) == 1 and isinstance (dst [0], list):
            # Unpack the first square bracket
                dst =  dst[0]
        else:
            dst = [nat_data['src-nat-rule-match'].get('destination-address')]
        try:
            src = [nat_data['src-nat-rule-match'].get('source-address')]
        except:
            src = nat_data['src-nat-rule-match'].get('source-address')
        # Get the source-nat action of the rule
        action = nat_data['then']['source-nat']
        # Append the name, destination address, source address, and action to the result list
        result.append([name, dst, src, action])
    except:
        for rule in nat_data:
            name = rule['name']
            dst = [rule['src-nat-rule-match'].get('destination-address')]
            if len (dst) == 1 and isinstance (dst [0], list):
            # Unpack the first square bracket
                dst =  dst[0]
            else:
                dst = [rule['src-nat-rule-match'].get('destination-address')]
        # Get the source address of the rule
            try:
                src = [rule['src-nat-rule-match'].get('source-address')]
                if len (src) == 1 and isinstance (src [0], list):
            # Unpack the first square bracket
                    src =  src[0]
            except:
                src = rule['src-nat-rule-match'].get('source-address')
            # Get the source-nat action of the rule
            action = rule['then']['source-nat']
            # Append the name, destination address, source address, and action to the result list
            result.append([name, dst, src, action])
    return result


