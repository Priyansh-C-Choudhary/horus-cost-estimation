"""
AWS Services Cost Calculation Package
Contains modules for calculating costs of various AWS services from Terraform configurations
"""

from . import ec2
from . import rds
from . import vpc
from . import nat as nat_gateway
from . import eip
from . import sg as security_groups

__all__ = [
    'ec2',
    'rds', 
    'vpc',
    'nat_gateway',  # <-- Corrected this line
    'eip',
    'security_groups'
]

# Version information
__version__ = '2.0.0'
__author__ = 'Terraform Cost Estimation Tool'
__description__ = 'AWS services cost calculation from Terraform configurations'

# Supported AWS services
SUPPORTED_SERVICES = {
    'aws_instance': 'EC2 Instances',
    'aws_db_instance': 'RDS Database Instances', 
    'aws_vpc': 'Virtual Private Cloud',
    'aws_subnet': 'VPC Subnets',
    'aws_internet_gateway': 'Internet Gateways',
    'aws_nat_gateway': 'NAT Gateways',
    'aws_eip': 'Elastic IP Addresses',
    'aws_security_group': 'Security Groups',
    'aws_security_group_rule': 'Security Group Rules',
    'aws_route_table': 'Route Tables',
    'aws_network_acl': 'Network ACLs'
}

def get_supported_services():
    """Return list of supported AWS services"""
    return list(SUPPORTED_SERVICES.keys())

def get_service_description(service_type: str) -> str:
    """Get human-readable description for a service type"""
    return SUPPORTED_SERVICES.get(service_type, 'Unknown Service')