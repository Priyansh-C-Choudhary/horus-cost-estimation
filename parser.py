"""
Enhanced Terraform Configuration Parser
Supports parsing multiple .tf files in a directory
"""

import os
import glob
import hcl2
from typing import Tuple, List, Dict, Any, Optional

def parse_terraform_file(file_path: str) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Parse a single Terraform file and extract region and resources
    
    Args:
        file_path: Path to the .tf file
        
    Returns:
        Tuple of (region, resources) or (None, []) if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Skip empty files
        if not content.strip():
            return None, []
            
        terraform_data = hcl2.loads(content)
        
        # Extract region from provider configuration
        region = None
        providers = terraform_data.get("provider", [])
        for provider in providers:
            if "aws" in provider:
                aws_config = provider["aws"]
                if isinstance(aws_config, dict):
                    region = aws_config.get("region")
                elif isinstance(aws_config, list) and aws_config:
                    region = aws_config[0].get("region")
                if region:
                    break
        
        # Extract resources
        resources = terraform_data.get("resource", [])
        
        return region, resources
        
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {str(e)}")
        return None, []

def find_terraform_files(directory_path: str) -> List[str]:
    """
    Find all .tf files in the given directory
    
    Args:
        directory_path: Path to search for .tf files
        
    Returns:
        List of .tf file paths
    """
    tf_files = []
    
    # Use glob to find all .tf files
    pattern = os.path.join(directory_path, "*.tf")
    tf_files.extend(glob.glob(pattern))
    
    # Also check subdirectories (non-recursive for now)
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            subdir_pattern = os.path.join(item_path, "*.tf")
            tf_files.extend(glob.glob(subdir_pattern))
    
    return sorted(tf_files)

def merge_resources(all_resources: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge resources from multiple files into a single list
    
    Args:
        all_resources: List of resource lists from different files
        
    Returns:
        Merged list of all resources
    """
    merged = []
    
    for resource_list in all_resources:
        merged.extend(resource_list)
    
    return merged

def extract_variables(terraform_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract variable definitions from Terraform data
    
    Args:
        terraform_data: Parsed Terraform configuration
        
    Returns:
        Dictionary of variables
    """
    variables = {}
    
    var_blocks = terraform_data.get("variable", [])
    for var_block in var_blocks:
        for var_name, var_config in var_block.items():
            default_value = var_config.get("default")
            variables[var_name] = default_value
    
    return variables

def parse_terraform_directory(directory_path: str) -> Tuple[Optional[str], List[Dict[str, Any]], List[str]]:
    """
    Parse all Terraform files in a directory
    
    Args:
        directory_path: Path to directory containing .tf files
        
    Returns:
        Tuple of (region, all_resources, parsed_files)
    """
    tf_files = find_terraform_files(directory_path)
    
    if not tf_files:
        print(f"No .tf files found in {directory_path}")
        return None, [], []
    
    print(f"Found {len(tf_files)} Terraform file(s):")
    for tf_file in tf_files:
        print(f"  - {os.path.basename(tf_file)}")
    print()
    
    region = None
    all_resources = []
    parsed_files = []
    all_variables = {}
    
    # Parse each file
    for tf_file in tf_files:
        file_region, resources = parse_terraform_file(tf_file)
        
        if file_region and not region:
            region = file_region
        
        if resources:
            all_resources.extend(resources)
        
        parsed_files.append(os.path.basename(tf_file))
        
        # Also extract variables for potential future use
        try:
            with open(tf_file, 'r', encoding='utf-8') as f:
                terraform_data = hcl2.load(f)
                variables = extract_variables(terraform_data)
                all_variables.update(variables)
        except:
            pass  # Continue if variable extraction fails
    
    return region, all_resources, parsed_files

def validate_terraform_config(directory_path: str) -> Dict[str, Any]:
    """
    Validate Terraform configuration and provide summary
    
    Args:
        directory_path: Path to Terraform directory
        
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'file_count': 0,
        'resource_count': 0,
        'resource_types': set()
    }
    
    try:
        region, resources, files = parse_terraform_directory(directory_path)
        
        validation_result['file_count'] = len(files)
        validation_result['resource_count'] = len(resources)
        
        if not region:
            validation_result['warnings'].append("No AWS region found in provider configuration")
        
        if not resources:
            validation_result['errors'].append("No resources found in Terraform files")
            validation_result['valid'] = False
        
        # Count resource types
        for resource in resources:
            for resource_type in resource.keys():
                validation_result['resource_types'].add(resource_type)
        
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append(f"Validation failed: {str(e)}")
    
    return validation_result

# Example usage and testing function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python parser.py <terraform_directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # Validate configuration
    validation = validate_terraform_config(directory)
    
    print("Terraform Configuration Validation:")
    print(f"Valid: {validation['valid']}")
    print(f"Files: {validation['file_count']}")
    print(f"Resources: {validation['resource_count']}")
    print(f"Resource Types: {', '.join(sorted(validation['resource_types']))}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if validation['errors']:
        print("Errors:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['valid']:
        region, resources, files = parse_terraform_directory(directory)
        print(f"\nRegion: {region}")
        print(f"Total Resources: {len(resources)}")