import hcl2
import os

def parse_terraform_config(file_path: str):
    try:
        with open(file_path, 'r') as f:
            terraform_data = hcl2.load(f)

        region = terraform_data.get("provider", [{}])[0].get("aws", {}).get("region")
        resources = terraform_data.get("resource", [])
        return region, resources

    except FileNotFoundError:
        print(f"Error: Terraform file not found at {file_path}")
    except Exception as e:
        print(f"Error parsing Terraform file: {e}")

    return None, None