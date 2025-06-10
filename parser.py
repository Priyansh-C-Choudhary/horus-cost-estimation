"""
Enhanced Terraform Configuration Parser
Supports parsing multiple .tf files in a directory and basic variable substitution.
"""

import os
import glob
import hcl2
import re
from typing import Tuple, List, Dict, Any, Optional

def substitute_variables(data: Any, variables: Dict[str, Any]) -> Any:
    """
    Recursively substitutes variables in the parsed Terraform data.
    
    Args:
        data: The data to process (can be a dict, list, or string).
        variables: A dictionary of variable names to their values.
        
    Returns:
        The data with variables substituted.
    """
    if isinstance(data, dict):
        return {k: substitute_variables(v, variables) for k, v in data.items()}
    if isinstance(data, list):
        return [substitute_variables(i, variables) for i in data]
    if isinstance(data, str):
        # Regex to find all occurrences of ${var.variable_name}
        var_pattern = r'\$\{var\.([a-zA-Z0-9_]+)\}'
        
        # Simple substitution for now. This doesn't handle complex expressions.
        def replacer(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))

        # If the whole string is just one variable, return the raw type (e.g., bool)
        match = re.fullmatch(var_pattern, data)
        if match:
            var_name = match.group(1)
            return variables.get(var_name, data)

        return re.sub(var_pattern, replacer, data)

    return data

def parse_terraform_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a single Terraform file.
    
    Args:
        file_path: Path to the .tf file.
        
    Returns:
        Parsed data as a dictionary or an empty dict if parsing fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.strip():
            return {}
        return hcl2.loads(content)
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {str(e)}")
        return {}

def find_terraform_files(directory_path: str) -> List[str]:
    """
    Find all .tf files in the given directory.
    """
    pattern = os.path.join(directory_path, "*.tf")
    return sorted(glob.glob(pattern))

def extract_variables(terraform_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract variable definitions with their default values.
    """
    variables = {}
    var_blocks = terraform_data.get("variable", [])
    for var_block in var_blocks:
        for var_name, var_config in var_block.items():
            # Terraform variables can have a list of defaults, hcl2 returns a list
            default_value = var_config.get("default")
            if isinstance(default_value, list) and len(default_value) > 0:
                 variables[var_name] = default_value[0]
            else:
                 variables[var_name] = default_value
    return variables

def parse_terraform_directory(directory_path: str) -> Tuple[Optional[str], List[Dict[str, Any]], List[str]]:
    """
    Parse all Terraform files in a directory, performing variable substitution.
    
    Args:
        directory_path: Path to directory containing .tf files.
        
    Returns:
        Tuple of (region, all_resources, parsed_files).
    """
    tf_files = find_terraform_files(directory_path)
    
    if not tf_files:
        print(f"No .tf files found in {directory_path}")
        return None, [], []
    
    print(f"Found {len(tf_files)} Terraform file(s):")
    for tf_file in tf_files:
        print(f"  - {os.path.basename(tf_file)}")
    print()

    all_data = []
    all_variables = {}

    # First pass: Parse all files and collect all variable definitions
    for tf_file in tf_files:
        data = parse_terraform_file(tf_file)
        if data:
            all_data.append(data)
            all_variables.update(extract_variables(data))

    # Second pass: Extract provider and resources, then substitute variables
    region = None
    all_resources = []
    
    for data in all_data:
        # Extract region from provider configuration
        if "provider" in data and not region:
            for provider in data["provider"]:
                if "aws" in provider:
                    aws_config = provider["aws"]
                    config_dict = aws_config[0] if isinstance(aws_config, list) else aws_config
                    raw_region = config_dict.get("region")
                    if raw_region:
                        # Substitute variable in region string itself
                        region = substitute_variables(raw_region, all_variables)
                        break
        
        # Extract resources
        if "resource" in data:
            all_resources.extend(data["resource"])

    # Substitute variables in all collected resources
    substituted_resources = substitute_variables(all_resources, all_variables)

    parsed_files = [os.path.basename(f) for f in tf_files]
    return region, substituted_resources, parsed_files