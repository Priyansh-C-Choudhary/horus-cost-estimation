"""
VPC Service Cost Calculator
Handles VPC, Subnets, Internet Gateways, Route Tables, and Network ACLs
"""
import boto3
import json
from typing import List, Dict, Any, Optional

def process_vpc(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ Process VPC resources - VPCs are free in AWS """
    details = []
    for res in resources:
        if 'aws_vpc' in res:
            for name, cfg in res['aws_vpc'].items():
                details.append({
                    'name': name, 'type': f"VPC ({cfg.get('cidr_block', 'N/A')})",
                    'monthly': 0.0, 'price_per_hour': 0.0
                })
    return {'type': 'VPC', 'total_hourly': 0.0, 'total_monthly': 0.0, 'instances': details}

def process_subnet(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ Process Subnet resources - Subnets are free in AWS """
    details = []
    for res in resources:
        if 'aws_subnet' in res:
            for name, cfg in res['aws_subnet'].items():
                subnet_type = 'Public' if cfg.get('map_public_ip_on_launch', False) else 'Private'
                details.append({
                    'name': name, 'type': f"{subnet_type} Subnet ({cfg.get('cidr_block', 'N/A')})",
                    'monthly': 0.0, 'price_per_hour': 0.0
                })
    return {'type': 'Subnet', 'total_hourly': 0.0, 'total_monthly': 0.0, 'instances': details}

def process_internet_gateway(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ Process Internet Gateway resources - IGWs are free in AWS """
    details = []
    for res in resources:
        if 'aws_internet_gateway' in res:
            for name, cfg in res['aws_internet_gateway'].items():
                details.append({'name': name, 'type': 'Internet Gateway', 'monthly': 0.0, 'price_per_hour': 0.0})
    return {'type': 'IGW', 'total_hourly': 0.0, 'total_monthly': 0.0, 'instances': details}

def process_route_table(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ Process Route Table resources - Route Tables are free in AWS """
    details = []
    for res in resources:
        if 'aws_route_table' in res:
            for name, cfg in res['aws_route_table'].items():
                route_count = len(cfg.get('route', []))
                details.append({
                    'name': name, 'type': f'Route Table ({route_count} routes)',
                    'monthly': 0.0, 'price_per_hour': 0.0
                })
    return {'type': 'Route Table', 'total_hourly': 0.0, 'total_monthly': 0.0, 'instances': details}

def process_network_acl(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ Process Network ACL resources - NACLs are free in AWS """
    details = []
    for res in resources:
        if 'aws_network_acl' in res:
            for name, cfg in res['aws_network_acl'].items():
                ingress_count = len(cfg.get('ingress', []))
                egress_count = len(cfg.get('egress', []))
                details.append({
                    'name': name, 'type': f'Network ACL ({ingress_count}I/{egress_count}E rules)',
                    'monthly': 0.0, 'price_per_hour': 0.0
                })
    return {'type': 'NACL', 'total_hourly': 0.0, 'total_monthly': 0.0, 'instances': details}


def get_vpc_endpoint_price(region: str, endpoint_type: str = 'Gateway') -> float:
    """ Get VPC Endpoint pricing (Interface endpoints have costs, Gateway endpoints are free) """
    if endpoint_type.lower() == 'gateway':
        return 0.0

    try:
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        region_mapping = {'us-west-2': 'US West (Oregon)', 'us-east-1': 'US East (N. Virginia)'}
        location = region_mapping.get(region, region)

        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'VPC Endpoint'},
            {'Type': 'TERM_MATCH', 'Field': 'usagetype', 'Value': f"{region}-InterfaceEndpoint-Hours"}
        ]
        response = pricing_client.get_products(ServiceCode='AmazonVPC', Filters=filters)
        if not response['PriceList']: return 0.01
        
        price_item = json.loads(response['PriceList'][0])
        terms = price_item['terms']['OnDemand']
        price_dimensions = list(terms.values())[0]['priceDimensions']
        return float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
    except Exception as e:
        print(f"Error fetching VPC Endpoint price: {e}")
        return 0.01

def process_vpc_endpoint(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ Process VPC Endpoint resources """
    details = []
    total_hourly = 0.0
    
    for res in resources:
        if 'aws_vpc_endpoint' in res:
            for name, cfg in res['aws_vpc_endpoint'].items():
                vpc_endpoint_type = cfg.get('vpc_endpoint_type', 'Gateway')
                price_per_hour = get_vpc_endpoint_price(region, vpc_endpoint_type)
                monthly = price_per_hour * 730
                
                details.append({
                    'name': name,
                    'type': f'{vpc_endpoint_type} VPC Endpoint',
                    'price_per_hour': price_per_hour,
                    'monthly': monthly
                })
                total_hourly += price_per_hour
    
    return {
        'type': 'VPC Endpoint',
        'total_hourly': total_hourly,
        'total_monthly': total_hourly * 730,
        'instances': details
    }