import boto3
import json
from typing import List, Dict, Any, Optional

class EIPPriceFetcher:
    def __init__(self, region: str):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.region_mapping = {
            'us-east-1': 'US East (N. Virginia)', 'us-east-2': 'US East (Ohio)',
            # ... (add other regions if needed, but not strictly necessary for this)
        }
        self.location = self.region_mapping.get(self.region, self.region)
        self._price = None

    def get_unattached_eip_hourly_price(self) -> float:
        if self._price is not None:
            return self._price

        try:
            # Note: The filter is for "per IP" not in use.
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.location},
                {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'IP Address'},
                {'Type': 'TERM_MATCH', 'Field': 'usagetype', 'Value': f"{self.region}-ElasticIP:IdleAddress"}
            ]
            response = self.pricing_client.get_products(ServiceCode='AmazonVPC', Filters=filters)
            if not response['PriceList']: return 0.005

            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            self._price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            return self._price
        except Exception as e:
            print(f"Error fetching EIP price: {e}")
            return 0.005 # Fallback default

def process_eip(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    fetcher = EIPPriceFetcher(region)
    total_hourly = 0.0
    details = []
    
    for res in resources:
        if 'aws_eip' in res:
            for name, cfg in res['aws_eip'].items():
                is_for_nat_gateway = 'nat' in name.lower() or 'nat_gateway' in str(cfg.get('depends_on', ''))
                is_attached = bool(cfg.get('instance') 
                   or cfg.get('network_interface') 
                   or cfg.get('association_id') 
                   or is_for_nat_gateway)
                
                hourly_price = 0.0 if is_attached else fetcher.get_unattached_eip_hourly_price()
                monthly_cost = hourly_price * 730
                
                status = "Attached (FREE)" if is_attached else "Unattached (CHARGED)"
                
                details.append({
                    'name': name,
                    'type': 'Elastic IP',
                    'status': status,
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