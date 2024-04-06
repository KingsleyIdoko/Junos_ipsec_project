def gen_ikepolicy_config(old_ike_names):
    if old_ike_names:
        payload = f"""
        <configuration>
                <security>
                    <ike>
                        <policy>
                            <name>ikepolicy1</name>
                            <description operation="delete"/>
                            <description operation="create">ikepolic2</description>
                            <proposals insert="after"  key="[ name='IKEPROPOSAL_2' ]" operation="create">IKEPROPOSAL_3</proposals>
                            <proposals insert="after"  key="[ name='IKEPROPOSAL_3' ]" operation="create">IKE_PROPOSAL_3</proposals>
                            <pre-shared-key>
                                <ascii-text operation="delete"/>
                                <ascii-text operation="create">$9$NIbwgiHmTF/s2mTzF/9evMXdb</ascii-text>
                            </pre-shared-key>
                        </policy>
                    </ike>
                </security>
        </configuration>""".strip()
    else:
        payload =f""" 
            <configuration>
                <security>
                    <ike>
                        <policy operation="create">
                            <name>ikepolicy1</name>
                            <mode>main</mode>
                            <description>ikepolicy1</description>
                            <proposals>IKEPROPOSAL_2</proposals>
                            <pre-shared-key>
                                <ascii-text>$9$pYP/OIhevLVwgSrwgoJHkp0B1IhrlKMLxhcwY</ascii-text>
                            </pre-shared-key>
                        </policy>
                    </ike>
                </security>
            </configuration>""".strip()