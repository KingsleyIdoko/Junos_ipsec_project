def select_prefix(source_prefixes):
    print("0. None")
    for i, prefix in enumerate(source_prefixes, 1):
        print(f"{i}. {prefix}")
    while True: 
        selected_indexes = input("Your selection(s): ")
        selected_sources = []
        try:
            indexes = [int(x.strip()) for x in selected_indexes.split(',') if x.strip().isdigit()]
            if 0 in indexes and len(indexes) > 1:
                print("Invalid selection. You cannot select 'None' along with other options.")
                continue 
            elif 0 in indexes:
                return [] 
            valid_indexes = all(1 <= index <= len(source_prefixes) for index in indexes)
            if not valid_indexes:
                print(f"Please select a valid number between 1 and {len(source_prefixes)}.")
                continue  
            for index in indexes:
                selected_sources.append(source_prefixes[index - 1])
            break 
        except ValueError:
            print("Invalid input. Please enter numbers only.")
    return selected_sources






