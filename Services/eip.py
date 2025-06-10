"""
Elastic IP Service Cost Calculator
Handles EIP pricing - EIPs are free when attached to running instances, 
but charged when unattached or attached to stopped instances
"""

from typing import List, Dict, Any

class EIPPriceFetcher:
    def __init__(self, region: str):
        self.region = region
        
        # EIP pricing is generally consistent across regions
        # Charged when EIP is not associated with a running instance
        self.eip_hourly_rates = {
            'us-east-1': 0.005,      # $0.005 per hour when not attached
            'us-east-2': 0.005,
            'us-west-1': 0.005,
            'us-west-2': 0.005,
            'ca-central-1': 0.005,
            'eu-west-1': 0.005,
            'eu-west-2': 0.005,
            'eu-west-3': 0.005,
            'eu-central-1': 0.005,
            'eu-north-1': 0.005,
            'ap-southeast-1': 0.005,
            'ap-southeast-2': 0.005,
            'ap-northeast-1': 0.005,
            'ap-northeast-2': 0.005,
            'ap-south-1': 0.005,
            'sa-east-1': 0.005,
        }
    
    def get_eip_hourly_price(self, is_attached: bool = True) -> float:
        """
        Get EIP hourly price
        
        Args:
            is_attached: Whether EIP is attached to a running instance
            
        Returns:
            Hourly price (0.0 if attached, charge if not attached)
        """
        if is_attached:
            return 0.0  # Free when attached to running instance
        else:
            return self.eip_hourly_rates.get(self.region, 0.005)

def process_eip(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Elastic IP resources
    
    Args:
        region: AWS region
        resources: List of EIP resources
        
    Returns:
        Dictionary with cost information
    """
    fetcher = EIPPriceFetcher(region)
    total_hourly = 0.0
    details = []
    
    for res in resources:
        if 'aws_eip' in res:
            for name, cfg in res['aws_eip'].items():
                # Check if EIP is associated with an instance
                instance_id = cfg.get('instance')
                network_interface_id = cfg.get('network_interface')
                associate_with_private_ip = cfg.get('associate_with_private_ip')
                
                # Determine if EIP is attached
                is_attached = bool(instance_id or network_interface_id)
                
                # Get pricing
                hourly_price = fetcher.get_eip_hourly_price(is_attached)
                monthly_cost = hourly_price * 730
                
                # Determine EIP type
                eip_type = "VPC" if cfg.get('vpc', True) else "EC2-Classic"
                
                status = "Attached (FREE)" if is_attached else "Unattached (CHARGED)"
                
                details.append({
                    'name': name,
                    'type': f'Elastic IP ({eip_type})',
                    'status': status,
                    'is_attached': is_attached,
                    'instance_id': instance_id or 'N/A',
                    'network_interface_id': network_interface_id or 'N/A',
                    'price_per_hour': hourly_price,
                    'monthly': monthly_cost
                })
                
                total_hourly += hourly_price
    
    total_monthly = total_hourly * 730
    
    return {
        'type': 'Elastic IP',
        'total_hourly': total_hourly,
        'total_monthly': total_monthly,
        'instances': details
    }

def process_eip_association(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process EIP Association resources
    Note: EIP associations don't have separate costs, the cost is in the EIP itself
    
    Args:
        region: AWS region
        resources: List of EIP Association resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_eip_association' in res:
            for name, cfg in res['aws_eip_association'].items():
                instance_id = cfg.get('instance_id', 'N/A')
                allocation_id = cfg.get('allocation_id', 'N/A')
                
                details.append({
                    'name': name,
                    'type': 'EIP Association',
                    'instance_id': instance_id,
                    'allocation_id': allocation_id,
                    'price_per_hour': 0.0,  # No separate charge for association
                    'monthly': 0.0
                })
    
    return {
        'type': 'EIP Association',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

# Additional utility functions for EIP cost analysis

def estimate_eip_costs_scenario(num_eips: int, percent_attached: float = 0.8, region: str = 'us-east-1') -> Dict[str, float]:
    """
    Estimate EIP costs for different scenarios
    
    Args:
        num_eips: Total number of EIPs
        percent_attached: Percentage of EIPs that are attached (0.0 to 1.0)
        region: AWS region
        
    Returns:
        Dictionary with cost breakdown
    """
    fetcher = EIPPriceFetcher(region)
    
    attached_eips = int(num_eips * percent_attached)
    unattached_eips = num_eips - attached_eips
    
    attached_hourly = attached_eips * fetcher.get_eip_hourly_price(True)
    unattached_hourly = unattached_eips * fetcher.get_eip_hourly_price(False)
    
    total_hourly = attached_hourly + unattached_hourly
    total_monthly = total_hourly * 730
    
    return {
        'total_eips': num_eips,
        'attached_eips': attached_eips,
        'unattached_eips': unattached_eips,
        'attached_hourly_cost': attached_hourly,
        'unattached_hourly_cost': unattached_hourly,
        'total_hourly_cost': total_hourly,
        'total_monthly_cost': total_monthly
    }