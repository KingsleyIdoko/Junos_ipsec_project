import re
from ipaddress import ip_network

def compare_nat(payload):
    # Create a list to store the groups of rules
    collect_dup_rules = []

    # Loop through the payload list
    for i in range(len(payload)):
        # Get the first rule dictionary
        rule1 = payload[i]

        # Loop through the rest of the list
        for j in range(i + 1, len(payload)):
            # Get the second rule dictionary
            rule2 = payload[j]

            # Compare the source-address and destination-address values
            if (
                rule1['src-nat-rule-match'].get('source-address') == rule2['src-nat-rule-match'].get('source-address')
                and rule1['src-nat-rule-match'].get('destination-address') == rule2['src-nat-rule-match'].get('destination-address')
            ):
                # Append the names of the rules that have similar values to the list of groups
                collect_dup_rules.append([rule1['name'], rule2['name']])

    # Return the list of groups as the result
    return collect_dup_rules

def first_duplicate_rule(rules):
    # Create a new list to store the highest rules in each group
    highest_rules = []

    # Loop through the list of groups
    for group in rules:
        # Initialize the highest rule as the first element of the group
        highest_rule = group[0]

        # Loop through the rest of the group
        for rule in group[1:]:
            # Compare the rule names by removing the 'rule' prefix and converting to integers
            if int(rule[4:]) > int(highest_rule[4:]):
                # Update the highest rule if the current rule is higher
                highest_rule = rule

        # Append the highest rule to the new list
        highest_rules.append(highest_rule)

    # Return the new list as the result
    return highest_rules


def filter_list(payload):
    # Create a new list to store the items without duplicates
    list_without_duplicates = []

    # Loop through the original list
    for item in payload:
        # Check if the item is not in the new list
        if item not in list_without_duplicates:
            # Append the item to the new list
            list_without_duplicates.append(item)

    # Print the new list
    return list_without_duplicates


def nat_delete(rule, rule_set_name):
    payload = f"""
    <configuration>
            <security>
                <nat>
                    <source>
                        <rule-set>
                            <name>{rule_set_name}</name>
                            <rule operation="delete">
                                <name>{rule}</name>
                            </rule>
                        </rule-set>
                    </source>
                </nat>
            </security>
    </configuration>"""
    return payload


# Define a function to calculate the length of a prefix
def prefix_length(prefix):
    # Check if the prefix is None
    if prefix is None:
        # Return a default value, such as 0
        return 0
    # Otherwise, split the prefix by the slash
    parts = prefix.split('/')
    # If there is no slash, the length is 32
    if len(parts) == 1:
        return 32
    # Otherwise, the length is the number after the slash
    else:
        return int(parts[1])

def prefix_compare(prefix1, prefix2):
    # Check if the prefix1 is None
    if prefix1 is None:
        # Return a default value, such as 0
        num1 = 0
    # Otherwise, convert the prefix1 to an integer by removing the dots and slashes
    else:
        num1 = int(prefix1.replace('.', '').replace('/', ''))
    
    # Do the same for prefix2
    if prefix2 is None:
        num2 = 0
    else:
        num2 = int(prefix2.replace('.', '').replace('/', ''))

    # Compare the numerical values of the prefixes
    return num1 - num2


def destination_sort_key(rule):
    dst = rule["src-nat-rule-match"].get("destination-address")
    if isinstance(dst, list):
        # Find the most specific (smallest prefix length, which is a larger number) and count of prefixes
        specificity = min((32 - ip_network(addr, strict=False).prefixlen for addr in dst), default=0)
        prefix_count = len(dst)
        # Ensuring lists are considered, but also using count as a tiebreaker (more prefixes = less specific)
        return (1, specificity, prefix_count)
    else:
        # Single address: more specific, especially 0.0.0.0/0
        if dst == "0.0.0.0/0":
            # Least specific possible, treated specially
            return (2, 0, 1)  # Count is irrelevant here but needed for consistent return structure
        network = ip_network(dst, strict=False)
        # More specific than any list, and 32 - prefixlen for specificity. Count is 1 for single addresses.
        return (0, 32 - network.prefixlen, 1)




def re_order_nat_policy(list_nat_rules, rule_set_name):
    # Create an empty list to store the nat elements
    nat_elements = []
    # Create a variable to store the previous rule name, and initialize it as None
    prev_rule = None
    # Get the last rule name from the list_nat_rules
    last_rule = list_nat_rules[-1]
    # Loop through the list of rules
    for rule in list_nat_rules:
        # Check if the rule name is the same as the last rule name
        if rule == last_rule:
            # Skip this rule
            continue
        # Otherwise, create a policy element with the rule name
        policy_element = f"""
                            <rule operation="merge">
                                <name>{rule}</name>
                            </rule>"""
        # Check if the previous rule is None
        if prev_rule is None:
            # Use 'first' as the insert attribute
            policy_element = policy_element.replace('<rule', '<rule insert="first"')
        else:
            # Use 'after' and the previous rule name as the key
            policy_element = policy_element.replace('<rule', f'<rule insert="after" key="[ name=\'{prev_rule}\' ]"')
        # Update the previous rule name with the current rule name
        prev_rule = rule
        # Append the policy element to the list of nat elements
        nat_elements.append(policy_element)
    # After the loop, append the last rule as the last element of the list of nat elements
    nat_elements.append(f"""
                            <rule insert="last" operation="merge">
                                <name>{rule}</name>
                            </rule>""")
    # Join the list of nat elements with newlines
    nat_elements = "\n".join(nat_elements)

    # Create the payload with the nat elements
    payload = f"""    
    <configuration>
            <security>
                <nat>
                    <source>
                        <rule-set>
                            <name>{rule_set_name}</name>
                            {nat_elements}
                        </rule-set>
                    </source>
                </nat>
            </security>
    </configuration>"""
    return payload



def sort_rules(rule_list):
    def extract_rule_number(rule):
        match = re.match(r'rule(\d+)', rule)
        return int(match.group(1)) if match else float('inf')

    return sorted(rule_list, key=extract_rule_number)


# Define a function to rename the NAT rules
def modify_nat_rule(rules):
    # Create a dictionary that maps the old rule names to the new rule names
    name_map = dict([('rule1', 'rule2'), ('rule2', 'rule1'), ('rule3', 'rule4'), ('rule4', 'rule3')])
    
    # Sort the list of dictionaries by the rule name
    rules = sorted(rules, key=lambda d: d['name'])
    
    # Loop through the rules
    for rule in rules:
        # Get the old rule name
        old_name = rule['name']
        
        # Get the new rule name from the dictionary, or use the old name if not found
        new_name = name_map.get(old_name, old_name)
        
        # Assign the new rule name to the rule
        rule['name'] = new_name

    # Return the renamed rules
    return rules









