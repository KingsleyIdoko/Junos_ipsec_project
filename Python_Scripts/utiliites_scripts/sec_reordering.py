def re_order_policy(zone_a, zone_b,closest_policies):
    # Use a list to store the policy elements
    policy_elements = []

    # Loop through the closest policies
    for index, closest_policy in enumerate(closest_policies, start=1):
        # Create a policy element with the insert and key attributes
        if index < len(closest_policies):
            next_policy = closest_policies[index]
            if closest_policies != next_policy:
                policy_element = f"""
                         <policy insert="after"  key="[ name='{closest_policy}' ]" operation="merge">
                            <name>{next_policy}</name>
                         </policy>"""
                # Append the policy element to the list
                policy_elements.append(policy_element)
    # Join the policy elements with a newline character
    policy_elements = "\n".join(policy_elements)

    # Create the payload with the policy elements
    payload = f"""    
        <configuration>
                <security>
                    <policies>
                        <policy>
                                <from-zone-name>{zone_a}</from-zone-name>
                                <to-zone-name>{zone_b}</to-zone-name>
                                {policy_elements}
                        </policy>
                    </policies>
                </security>
        </configuration>"""
    return payload