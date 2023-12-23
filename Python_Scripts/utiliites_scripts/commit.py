from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff

def run_pyez_tasks(self, payload, data_format):
    # Run the pyez_config task and store the response
    response = self.nr.run(task=pyez_config, payload=payload, data_format=data_format)
    for res in response:
        print(response[res].result)

    # Run the pyez_diff task and store the diff result
    diff_result = self.nr.run(task=pyez_diff)
    # Print the diff result
    committed = None
    for res in diff_result:
        # Check if the diff result is None
        if diff_result[res].result is None:
            # Print no config change and return
            print("No Config Change: No Commit to Apply")
        # Otherwise, print the diff result
        else:
            print(diff_result[res].result)
            # Run the pyez_commit task and store the committed result
            committed = self.nr.run(task=pyez_commit)
            for res in committed:
                print(committed[res].result)
    return response, committed
