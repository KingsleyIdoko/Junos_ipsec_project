from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff, pyez_rollback

def run_pyez_tasks(self, payload, data_format):
    response = self.nr.run(task=pyez_config, payload=payload, data_format=data_format)
    for res in response.values():  
        print(res.result)
    
    diff_result = self.nr.run(task=pyez_diff)
    need_commit = False

    for res in diff_result.values():
        if res.result:  
            print(res.result)
            need_commit = True
        else:
            print("No Config Change: No Commit to Apply")
    
    if need_commit:
        while True:
            message = input("Enter 'yes' to commit, 'no' to abort: ").lower()
            if message in ['yes', 'y']:
                committed = self.nr.run(task=pyez_commit)
                for res in committed.values():
                    print(res.result)
                return response, committed
            elif message in ['no', 'n']:
                rolled_back = self.nr.run(task=pyez_rollback)
                print("Configuration abort initiated.")
                return None
            else:
                print("Invalid command. Please enter 'yes', 'y', 'no', or 'n'.")
    else:
        return response, None

