import json

def load_mapping(json_path='fip_madmp_mapping.json'):
    with open(json_path, 'r') as file:
        return json.load(file)

# Quick verification, remove/comment out after verifying initially.
# if __name__ == "__main__":
   #  mapping_data = load_mapping()
    # print(json.dumps(mapping_data, indent=4))
