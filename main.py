import os
import sys
import argparse
from typing import Dict, List, Any
from parser import parse_terraform_directory
from Services import ec2, rds, vpc, eip, nat, security_groups

# Note: Renamed nat_gateway to nat to match the module filename
SERVICE_MAP = {
    'aws_instance': ec2.process_ec2,
    'aws_db_instance': rds.process_rds,
    'aws_vpc': vpc.process_vpc,
    'aws_subnet': vpc.process_subnet,
    'aws_internet_gateway': vpc.process_internet_gateway,
    'aws_nat_gateway': nat.process_nat_gateway,
    'aws_eip': eip.process_eip,
    'aws_security_group': security_groups.process_security_group,
    'aws_route_table': vpc.process_route_table,
    'aws_network_acl': vpc.process_network_acl,
    'aws_vpc_endpoint': vpc.process_vpc_endpoint
}

def print_banner():
    print("=" * 60 + "\n          TERRAFORM COST ESTIMATION TOOL\n" + "=" * 60 + "\n")

def print_cost_summary(results: List[Dict[str, Any]]):
    print("\n" + "=" * 60 + "\n             COST BREAKDOWN\n" + "=" * 60)
    total_hourly = 0.0
    total_monthly = 0.0
    
    for result in results:
        if result['instances']:
            print(f"\n--- {result['type']} ---")
            for instance in result['instances']:
                name = instance.get('name', 'Unknown')
                itype = instance.get('type', 'N/A')
                price_hr = instance.get('price_per_hour', 0) or 0
                monthly = instance.get('monthly', 0) or 0
                
                if monthly > 0 or result['type'] not in ['VPC', 'Subnet', 'IGW', 'Route Table', 'NACL', 'Security Group']:
                    details_str = f"| ${price_hr:.4f}/hr | ${monthly:.2f}/mo"
                    if result['type'] == 'EC2':
                        storage = instance.get('storage_info', '')
                        details_str += f" (Instance: ${instance.get('monthly_instance', 0):.2f}, Storage: ${instance.get('monthly_storage', 0):.2f})"
                        print(f"  {name:<20} | {itype:<15} | {storage:<12} {details_str}")
                    elif result['type'] == 'RDS':
                        storage = instance.get('storage_info', '')
                        multi_az = " (Multi-AZ)" if instance.get('multi_az') else ""
                        details_str += f" (Instance: ${instance.get('monthly_instance', 0):.2f}, Storage: ${instance.get('monthly_storage', 0):.2f})"
                        print(f"  {name:<20} | {itype:<15} | {instance.get('engine')}{multi_az:<10} | {storage:<12} {details_str}")
                    elif result['type'] == 'NAT Gateway':
                        gb = instance.get('estimated_data_gb')
                        print(f"  {name:<20} | {itype:<15} | {gb}GB/mo est. data | ${price_hr:.4f}/hr | ${monthly:.2f}/mo")
                    else:
                        print(f"  {name:<20} | {itype:<15} {details_str}")
                else:
                    print(f"  {name:<20} | {itype:<15} | FREE")

            total_hourly += result['total_hourly']
            total_monthly += result['total_monthly']
            
    print("\n" + "=" * 60)
    print(f"TOTAL HOURLY COST:  ${total_hourly:.4f} (compute only)")
    print(f"TOTAL MONTHLY COST: ${total_monthly:.2f}")
    print(f"TOTAL YEARLY COST:  ${total_monthly * 12:.2f}")
    print("=" * 60)
    print("\nDisclaimer: This is an estimate. Costs for data transfer, API requests,")
    print("and other services are not included. Verify with AWS Cost Explorer.")

def process_terraform_directory(directory_path: str, nat_gb_estimate: int) -> None:
    print(f"Analyzing Terraform files in: {directory_path}")
    print("-" * 50)
    
    region, all_resources, parsed_files = parse_terraform_directory(directory_path)
    
    if not region:
        print("\nError: No AWS region found. Ensure provider config includes a region.")
        sys.exit(1)
    if not all_resources:
        print("\nError: No resources found in Terraform files.")
        sys.exit(1)
    
    print(f"Parsed files: {', '.join(parsed_files)}")
    print(f"Detected AWS Region: {region}")
    print(f"Total resource blocks found: {len(all_resources)}")
    print()
    
    results = []
    for service_key, handler in SERVICE_MAP.items():
        filtered_resources = [r for r in all_resources if service_key in r]
        if filtered_resources:
            print(f"Processing {service_key}...")
            try:
                if service_key == 'aws_nat_gateway':
                    result = handler(region, filtered_resources, nat_gb_estimate)
                else:
                    result = handler(region, filtered_resources)
                results.append(result)
            except Exception as e:
                print(f"  -> Error processing {service_key}: {e}")

    if results:
        print_cost_summary(results)
    else:
        print("No supported resources found for cost calculation.")

def main():
    parser = argparse.ArgumentParser(description='Terraform Cost Estimation Tool')
    parser.add_argument('directory', help='Path to directory containing Terraform files')
    parser.add_argument('--nat-gb', type=int, default=100, help='Estimated monthly GB of data processed by NAT Gateways (default: 100)')
    args = parser.parse_args()
    
    print_banner()
    
    try:
        process_terraform_directory(args.directory, args.nat_gb)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()