"""
Enhanced Terraform Cost Estimation Tool
Supports multiple files, CLI interface, and extended AWS services
"""

import os
import sys
import argparse
from typing import Dict, List, Any
from parser import parse_terraform_directory
from Services import ec2, rds, vpc, eip, nat_gateway, security_groups

# Service mapping for different Terraform resources
SERVICE_MAP = {
    'aws_instance': ec2.process_ec2,
    'aws_db_instance': rds.process_rds,
    'aws_vpc': vpc.process_vpc,
    'aws_subnet': vpc.process_subnet,
    'aws_internet_gateway': vpc.process_internet_gateway,
    'aws_nat_gateway': nat_gateway.process_nat_gateway,
    'aws_eip': eip.process_eip,
    'aws_security_group': security_groups.process_security_group,
    'aws_route_table': vpc.process_route_table,
    'aws_network_acl': vpc.process_network_acl
}

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("          TERRAFORM COST ESTIMATION TOOL")
    print("=" * 60)
    print()

def print_cost_summary(results: List[Dict[str, Any]]):
    """Print detailed cost summary"""
    print("\n" + "=" * 50)
    print("             COST BREAKDOWN")
    print("=" * 50)
    
    total_hourly = 0.0
    total_monthly = 0.0
    
    for result in results:
        if result['instances']:  # Only show services with instances
            print(f"\n--- {result['type']} ---")
            
            for instance in result['instances']:
                name = instance.get('name', 'Unknown')
                instance_type = instance.get('type', 'N/A')
                price_per_hour = instance.get('price_per_hour', 0) or 0
                monthly_cost = instance.get('monthly', 0) or 0
                
                # Handle special cases for different service types
                if result['type'] == 'RDS':
                    engine = instance.get('engine', 'Unknown')
                    multi_az = " (Multi-AZ)" if instance.get('multi_az') else ""
                    print(f"  {name:<20} | {instance_type:<15} | {engine}{multi_az:<10} | ${price_per_hour:.4f}/hr | ${monthly_cost:.2f}/mo")
                elif result['type'] in ['VPC', 'Subnet', 'IGW', 'Route Table', 'NACL', 'Security Group']:
                    # These services are typically free or have minimal costs
                    print(f"  {name:<20} | {instance_type:<15} | FREE")
                else:
                    print(f"  {name:<20} | {instance_type:<15} | ${price_per_hour:.4f}/hr | ${monthly_cost:.2f}/mo")
            
            total_hourly += result['total_hourly']
            total_monthly += result['total_monthly']
    
    print("\n" + "=" * 50)
    print(f"TOTAL HOURLY COST:  ${total_hourly:.4f}")
    print(f"TOTAL MONTHLY COST: ${total_monthly:.2f}")
    print(f"TOTAL YEARLY COST:  ${total_monthly * 12:.2f}")
    print("=" * 50)

def process_terraform_directory(directory_path: str) -> None:
    """Process all Terraform files in the given directory"""
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a directory.")
        sys.exit(1)
    
    print(f"Analyzing Terraform files in: {directory_path}")
    print("-" * 50)
    
    # Parse all Terraform files in the directory
    region, all_resources, parsed_files = parse_terraform_directory(directory_path)
    
    if not region:
        print("Error: No AWS region found in Terraform files.")
        print("Please ensure your provider configuration includes a region.")
        sys.exit(1)
    
    if not all_resources:
        print("Error: No resources found in Terraform files.")
        sys.exit(1)
    
    print(f"Parsed files: {', '.join(parsed_files)}")
    print(f"Detected AWS Region: {region}")
    print(f"Total resources found: {len(all_resources)}")
    print()
    
    # Process each service type
    results = []
    for service_key, handler in SERVICE_MAP.items():
        # Filter resources for this service type
        filtered_resources = [r for r in all_resources if service_key in r]
        
        if filtered_resources:
            print(f"Processing {len(filtered_resources)} {service_key} resource(s)...")
            try:
                result = handler(region, filtered_resources)
                results.append(result)
            except Exception as e:
                print(f"Error processing {service_key}: {str(e)}")
                continue
    
    # Print results
    if results:
        print_cost_summary(results)
    else:
        print("No supported resources found for cost calculation.")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='Terraform Cost Estimation Tool - Calculate AWS infrastructure costs from Terraform files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py /path/to/terraform/directory
  python main.py ./terraform-configs
  python main.py . --verbose
        """
    )
    
    parser.add_argument(
        'directory',
        help='Path to directory containing Terraform files (.tf)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--region',
        help='Override AWS region (if not specified in Terraform files)'
    )
    
    args = parser.parse_args()
    
    # Set up verbose mode
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Print banner
    print_banner()
    
    try:
        process_terraform_directory(args.directory)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()