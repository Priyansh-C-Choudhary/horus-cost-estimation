import os
import glob
import hcl2
import re
import copy
import logging
from typing import Tuple, List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_terraform_files(directory_path: str) -> List[str]:
    """Find all .tf files in the given directory."""
    pattern = os.path.join(directory_path, "*.tf")
    return sorted(glob.glob(pattern))

def parse_terraform_file(file_path: str) -> Dict[str, Any]:
    """Parse a single Terraform file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.strip():
            return {}
        return hcl2.loads(content)
    except Exception as e:
        logging.error(f"Could not parse {file_path}: {e}", exc_info=True)
        return {}

def extract_variables(terraform_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract variable definitions with their default values."""
    variables = {}
    var_blocks = terraform_data.get("variable", [])
    if not isinstance(var_blocks, list): 
        return variables

    for var_block in var_blocks:
        for var_name, var_config in var_block.items():
            default_value = var_config.get("default")
            if isinstance(default_value, list) and len(default_value) > 0:
                if len(default_value) == 1:
                    variables[var_name] = default_value[0]
                else:
                    variables[var_name] = default_value
            else:
                variables[var_name] = default_value
    return variables

def substitute_variables_with_index(data: Any, variables: Dict[str, Any], index: int) -> Any:
    """Recursively substitutes variables, now with support for count.index."""
    if isinstance(data, dict):
        return {k: substitute_variables_with_index(v, variables, index) for k, v in data.items()}
    if isinstance(data, list):
        return [substitute_variables_with_index(i, variables, index) for i in data]
    if not isinstance(data, str):
        return data

    processed_data = data.replace('${count.index}', str(index))
    var_pattern = r'\$\{var\.([a-zA-Z0-9_]+)\}'
    full_match = re.fullmatch(var_pattern, processed_data)
    if full_match:
        var_name = full_match.group(1)
        return variables.get(var_name, processed_data)

    array_index_pattern = r'\$\{var\.([a-zA-Z0-9_]+)\[count\.index\]\}'
    array_match = re.fullmatch(array_index_pattern, processed_data)
    if array_match:
        var_name = array_match.group(1)
        var_value = variables.get(var_name)
        if isinstance(var_value, list) and 0 <= index < len(var_value):
            return var_value[index]
        return processed_data

    def replacer(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))

    final_data = re.sub(var_pattern, replacer, processed_data)
    return final_data

def expand_counted_resources(resources: List[Dict[str, Any]], variables: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Expands resources that use the 'count' meta-argument with enhanced variable handling."""
    expanded_resources = []

    if not isinstance(resources, list):
        return []

    for i, resource_group in enumerate(resources):
        if not isinstance(resource_group, dict):
            continue
        
        for resource_type, resource_definitions in resource_group.items():
            if not isinstance(resource_definitions, dict):
                continue

            for resource_name, resource_config in resource_definitions.items():
                if not isinstance(resource_config, dict):
                    continue
                
                count_val = resource_config.get('count', 1)

                if isinstance(count_val, str):
                    count_val = substitute_variables_with_index(count_val, variables, 0)

                if isinstance(count_val, str) and 'length' in count_val:
                    length_pattern = r'\$\{length\(var\.([a-zA-Z0-9_]+)\)\}'
                    match = re.search(length_pattern, count_val)
                    if match:
                        var_name = match.group(1)
                        var_value = variables.get(var_name)
                        if var_value is not None:
                            if isinstance(var_value, list):
                                count_val = len(var_value)
                            else:
                                count_val = 1
                        else:
                            count_val = 1

                try:
                    instance_count = int(count_val)
                except (ValueError, TypeError):
                    instance_count = 1

                for i_loop in range(instance_count):
                    new_config = copy.deepcopy(resource_config)
                    if 'count' in new_config:
                        del new_config['count']
                    expanded_config = substitute_variables_with_index(new_config, variables, i_loop)
                    new_name = f"{resource_name}[{i_loop}]" if instance_count > 1 else resource_name
                    expanded_resources.append({resource_type: {new_name: expanded_config}})
    
    return expanded_resources

def parse_terraform_directory(directory_path: str) -> Tuple[Optional[str], List[Dict[str, Any]], List[str]]:
    """Parse all Terraform files, performing variable substitution and resource expansion."""
    tf_files = find_terraform_files(directory_path)
    if not tf_files:
        logging.error(f"No .tf files found in {directory_path}")
        return None, [], []
    
    # Step 1: Parse all files and gather all raw data and variables
    all_data, all_variables = [], {}
    for tf_file in tf_files:
        data = parse_terraform_file(tf_file)
        if data:
            all_data.append(data)
            all_variables.update(extract_variables(data))

    # Step 2: Extract region and all unexpanded resources
    region, unexpanded_resources = None, []
    for data in all_data:
        if not region and "provider" in data:
            provider_blocks = data.get("provider", [])
            if isinstance(provider_blocks, list):
                for provider in provider_blocks:
                    if "aws" in provider:
                        aws_provider_block = provider["aws"]
                        config_list = aws_provider_block if isinstance(aws_provider_block, list) else [aws_provider_block]
                        if config_list and isinstance(config_list[0], dict):
                            raw_region = config_list[0].get("region")
                            if raw_region:
                                region = substitute_variables_with_index(raw_region, all_variables, 0)
                                break
        if "resource" in data and isinstance(data["resource"], list):
            unexpanded_resources.extend(data["resource"])

    # Step 3: Expand counted resources
    final_resources = expand_counted_resources(unexpanded_resources, all_variables)

    parsed_files = [os.path.basename(f) for f in tf_files]
    return region, final_resources, parsed_files
