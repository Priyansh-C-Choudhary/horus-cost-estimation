"""
VPC Service Cost Calculator
Handles VPC, Subnets, Internet Gateways, Route Tables, and Network ACLs
"""

from typing import List, Dict, Any

def process_vpc(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process VPC resources - VPCs are free in AWS
    
    Args:
        region: AWS region
        resources: List of VPC resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_vpc' in res:
            for name, cfg in res['aws_vpc'].items():
                cidr_block = cfg.get('cidr_block', 'N/A')
                enable_dns_hostnames = cfg.get('enable_dns_hostnames', False)
                enable_dns_support = cfg.get('enable_dns_support', True)
                
                details.append({
                    'name': name,
                    'type': f'VPC ({cidr_block})',
                    'cidr_block': cidr_block,
                    'dns_hostnames': enable_dns_hostnames,
                    'dns_support': enable_dns_support,
                    'price_per_hour': 0.0,  # VPCs are free
                    'monthly': 0.0
                })
    
    return {
        'type': 'VPC',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

def process_subnet(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Subnet resources - Subnets are free in AWS
    
    Args:
        region: AWS region
        resources: List of Subnet resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_subnet' in res:
            for name, cfg in res['aws_subnet'].items():
                cidr_block = cfg.get('cidr_block', 'N/A')
                availability_zone = cfg.get('availability_zone', 'N/A')
                map_public_ip = cfg.get('map_public_ip_on_launch', False)
                subnet_type = 'Public' if map_public_ip else 'Private'
                
                details.append({
                    'name': name,
                    'type': f'{subnet_type} Subnet ({cidr_block})',
                    'cidr_block': cidr_block,
                    'availability_zone': availability_zone,
                    'public': map_public_ip,
                    'price_per_hour': 0.0,  # Subnets are free
                    'monthly': 0.0
                })
    
    return {
        'type': 'Subnet',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

def process_internet_gateway(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Internet Gateway resources - IGWs are free in AWS
    
    Args:
        region: AWS region
        resources: List of Internet Gateway resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_internet_gateway' in res:
            for name, cfg in res['aws_internet_gateway'].items():
                vpc_id = cfg.get('vpc_id', 'N/A')
                
                details.append({
                    'name': name,
                    'type': 'Internet Gateway',
                    'vpc_id': vpc_id,
                    'price_per_hour': 0.0,  # IGWs are free
                    'monthly': 0.0
                })
    
    return {
        'type': 'IGW',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

def process_route_table(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Route Table resources - Route Tables are free in AWS
    
    Args:
        region: AWS region
        resources: List of Route Table resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_route_table' in res:
            for name, cfg in res['aws_route_table'].items():
                vpc_id = cfg.get('vpc_id', 'N/A')
                routes = cfg.get('route', [])
                route_count = len(routes) if isinstance(routes, list) else 0
                
                details.append({
                    'name': name,
                    'type': f'Route Table ({route_count} routes)',
                    'vpc_id': vpc_id,
                    'route_count': route_count,
                    'price_per_hour': 0.0,  # Route Tables are free
                    'monthly': 0.0
                })
    
    return {
        'type': 'Route Table',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

def process_network_acl(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Network ACL resources - NACLs are free in AWS
    
    Args:
        region: AWS region
        resources: List of Network ACL resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_network_acl' in res:
            for name, cfg in res['aws_network_acl'].items():
                vpc_id = cfg.get('vpc_id', 'N/A')
                ingress_rules = cfg.get('ingress', [])
                egress_rules = cfg.get('egress', [])
                
                ingress_count = len(ingress_rules) if isinstance(ingress_rules, list) else 0
                egress_count = len(egress_rules) if isinstance(egress_rules, list) else 0
                
                details.append({
                    'name': name,
                    'type': f'Network ACL ({ingress_count}I/{egress_count}E rules)',
                    'vpc_id': vpc_id,
                    'ingress_rules': ingress_count,
                    'egress_rules': egress_count,
                    'price_per_hour': 0.0,  # NACLs are free
                    'monthly': 0.0
                })
    
    return {
        'type': 'NACL',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

# Additional VPC-related components that might have costs

def get_vpc_endpoint_price(region: str, endpoint_type: str = 'Gateway') -> float:
    """
    Get VPC Endpoint pricing (Interface endpoints have costs, Gateway endpoints are free)
    
    Args:
        region: AWS region
        endpoint_type: 'Gateway' or 'Interface'
        
    Returns:
        Price per hour
    """
    if endpoint_type.lower() == 'gateway':
        return 0.0  # Gateway endpoints (S3, DynamoDB) are free
    
    # Interface endpoints pricing (approximate)
    # This varies by region, these are rough estimates for us-east-1
    base_price = 0.01  # $0.01 per hour per VPC endpoint
    
    region_multipliers = {
        'us-east-1': 1.0,
        'us-east-2': 1.0,
        'us-west-1': 1.1,
        'us-west-2': 1.0,
        'eu-west-1': 1.1,
        'eu-central-1': 1.1,
        'ap-southeast-1': 1.2,
        'ap-northeast-1': 1.2,
    }
    
    multiplier = region_multipliers.get(region, 1.0)
    return base_price * multiplier

def process_vpc_endpoint(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process VPC Endpoint resources
    
    Args:
        region: AWS region
        resources: List of VPC Endpoint resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    total_hourly = 0.0
    
    for res in resources:
        if 'aws_vpc_endpoint' in res:
            for name, cfg in res['aws_vpc_endpoint'].items():
                service_name = cfg.get('service_name', 'N/A')
                vpc_endpoint_type = cfg.get('vpc_endpoint_type', 'Gateway')
                
                price_per_hour = get_vpc_endpoint_price(region, vpc_endpoint_type)
                monthly = price_per_hour * 730
                
                details.append({
                    'name': name,
                    'type': f'{vpc_endpoint_type} VPC Endpoint',
                    'service_name': service_name,
                    'endpoint_type': vpc_endpoint_type,
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