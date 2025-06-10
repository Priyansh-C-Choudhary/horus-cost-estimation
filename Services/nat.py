"""
NAT Gateway Service Cost Calculator
Handles NAT Gateway pricing which includes hourly charges and data processing charges
"""

import boto3
import json
from typing import List, Dict, Any, Optional

class NATGatewayPriceFetcher:
    def __init__(self, region: str):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        
        # NAT Gateway pricing is consistent across regions with some variations
        # These are approximate hourly rates (as of 2024)
        self.nat_gateway_hourly_rates = {
            'us-east-1': 0.045,      # $0.045 per hour
            'us-east-2': 0.045,
            'us-west-1': 0.048,
            'us-west-2': 0.045,
            'ca-central-1': 0.050,
            'eu-west-1': 0.048,
            'eu-west-2': 0.050,
            'eu-west-3': 0.051,
            'eu-central-1': 0.048,
            'eu-north-1': 0.043,
            'ap-southeast-1': 0.052,
            'ap-southeast-2': 0.052,
            'ap-northeast-1': 0.052,
            'ap-northeast-2': 0.052,
            'ap-south-1': 0.048,
            'sa-east-1': 0.058,
        }
        
        # Data processing charges (per GB processed)
        self.data_processing_rates = {
            'us-east-1': 0.045,      # $0.045 per GB
            'us-east-2': 0.045,
            'us-west-1': 0.048,
            'us-west-2': 0.045,
            'ca-central-1': 0.050,
            'eu-west-1': 0.048,
            'eu-west-2': 0.050,
            'eu-west-3': 0.051,
            'eu-central-1': 0.048,
            'eu-north-1': 0.043,
            'ap-southeast-1': 0.052,
            'ap-southeast-2': 0.052,
            'ap-northeast-1': 0.052,
            'ap-northeast-2': 0.052,
            'ap-south-1': 0.048,
            'sa-east-1': 0.058,
        }

    def get_nat_gateway_hourly_price(self) -> float:
        """Get NAT Gateway hourly price for the region"""
        return self.nat_gateway_hourly_rates.get(self.region, 0.045)  # Default to us-east-1 rate

    def get_data_processing_price(self) -> float:
        """Get data processing price per GB for the region"""
        return self.data_processing_rates.get(self.region, 0.045)  # Default to us-east-1 rate

    def estimate_monthly_data_processing_cost(self, estimated_gb_per_month: float = 100) -> float:
        """
        Estimate monthly data processing costs
        
        Args:
            estimated_gb_per_month: Estimated GB of data processed per month
            
        Returns:
            Monthly data processing cost
        """
        per_gb_rate = self.get_data_processing_price()
        return estimated_gb_per_month * per_gb_rate

def process_nat_gateway(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process NAT Gateway resources
    
    Args:
        region: AWS region
        resources: List of NAT Gateway resources
        
    Returns:
        Dictionary with cost information
    """
    fetcher = NATGatewayPriceFetcher(region)
    total_hourly = 0.0
    details = []
    
    for res in resources:
        if 'aws_nat_gateway' in res:
            for name, cfg in res['aws_nat_gateway'].items():
                subnet_id = cfg.get('subnet_id', 'N/A')
                allocation_id = cfg.get('allocation_id', 'N/A')
                connectivity_type = cfg.get('connectivity_type', 'public')
                
                # Get hourly price
                hourly_price = fetcher.get_nat_gateway_hourly_price()
                
                # Estimate data processing costs (default to 100GB/month)
                # In real scenarios, this would be based on actual usage patterns
                estimated_data_gb = 100  # Conservative estimate
                data_processing_monthly = fetcher.estimate_monthly_data_processing_cost(estimated_data_gb)
                
                # Total monthly cost = (hourly * 730) + data processing
                hourly_monthly = hourly_price * 730
                total_monthly = hourly_monthly + data_processing_monthly
                
                details.append({
                    'name': name,
                    'type': f'NAT Gateway ({connectivity_type})',
                    'subnet_id': subnet_id,
                    'connectivity_type': connectivity_type,
                    'price_per_hour': hourly_price,
                    'hourly_monthly': hourly_monthly,
                    'data_processing_monthly': data_processing_monthly,
                    'estimated_data_gb': estimated_data_gb,
                    'monthly': total_monthly
                })
                
                total_hourly += hourly_price
    
    total_monthly = sum(detail['monthly'] for detail in details)
    
    return {
        'type': 'NAT Gateway',
        'total_hourly': total_hourly,
        'total_monthly': total_monthly,
        'instances': details
    }

def process_nat_instance(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process NAT Instance resources (alternative to NAT Gateway using EC2)
    Note: NAT Instances are just EC2 instances, so cost is calculated via EC2 pricing
    
    Args:
        region: AWS region
        resources: List of NAT Instance resources (usually tagged EC2 instances)
        
    Returns:
        Dictionary with cost information
    """
    # NAT Instances are essentially EC2 instances
    # This is a placeholder - in practice, you'd identify NAT instances by tags
    # and process them through the EC2 pricing module
    
    details = []
    
    # This would typically be handled by the EC2 processor
    # but we can note them here for completeness
    
    return {
        'type': 'NAT Instance',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }