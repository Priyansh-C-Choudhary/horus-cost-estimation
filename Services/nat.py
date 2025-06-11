import boto3
import json
from typing import List, Dict, Any, Optional

class NATGatewayPriceFetcher:
    def __init__(self, region: str):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.region_mapping = {
            'us-east-1': 'US East (N. Virginia)', 'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)', 'us-west-2': 'US West (Oregon)',
            'ca-central-1': 'Canada (Central)', 'eu-west-1': 'Europe (Ireland)',
            'eu-west-2': 'Europe (London)', 'eu-west-3': 'Europe (Paris)',
            'eu-central-1': 'Europe (Frankfurt)', 'eu-north-1': 'Europe (Stockholm)',
            'ap-southeast-1': 'Asia Pacific (Singapore)', 'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)', 'ap-northeast-2': 'Asia Pacific (Seoul)',
            'ap-south-1': 'Asia Pacific (Mumbai)', 'sa-east-1': 'South America (Sao Paulo)'
        }
        self.location = self.region_mapping.get(self.region, self.region)
        self._price_cache = {}

    def _get_price(self, usage_type: str) -> Optional[float]:
        cache_key = usage_type
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]
        
        try:
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.location},
                {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'NAT Gateway'},
                {'Type': 'TERM_MATCH', 'Field': 'usagetype', 'Value': f"{self.region}-{usage_type}"}
            ]
            response = self.pricing_client.get_products(ServiceCode='AmazonVPC', Filters=filters)
            if not response['PriceList']:
                filters[2]['Value'] = usage_type
                response = self.pricing_client.get_products(ServiceCode='AmazonVPC', Filters=filters)
                if not response['PriceList']: return None

            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            self._price_cache[cache_key] = price
            return price
        except Exception as e:
            print(f"Error fetching NAT Gateway price for {usage_type}: {e}")
            return None
    
    def get_nat_gateway_hourly_price(self) -> float:
        return self._get_price('NatGateway-Hours') or 0.045

    def get_data_processing_price_per_gb(self) -> float:
        return self._get_price('NatGateway-Bytes') or 0.045

def process_nat_gateway(region: str, resources: List[Dict[str, Any]], estimated_gb_per_month: int = 100) -> Dict[str, Any]:
    fetcher = NATGatewayPriceFetcher(region)
    total_hourly = 0.0
    total_monthly = 0.0
    details = []
    
    for res in resources:
        if 'aws_nat_gateway' in res:
            for name, cfg in res['aws_nat_gateway'].items():
                hourly_price = fetcher.get_nat_gateway_hourly_price()
                data_processing_per_gb = fetcher.get_data_processing_price_per_gb()

                hourly_monthly_cost = hourly_price * 730
                data_proc_monthly_cost = data_processing_per_gb * estimated_gb_per_month
                total_instance_monthly = hourly_monthly_cost + data_proc_monthly_cost

                details.append({
                    'name': name,
                    'type': f'NAT Gateway',
                    'price_per_hour': hourly_price,
                    'data_processing_monthly': data_proc_monthly_cost,
                    'estimated_data_gb': estimated_gb_per_month,
                    'monthly': total_instance_monthly
                })
                
                total_hourly += hourly_price
                total_monthly += total_instance_monthly
    
    return {
        'type': 'NAT Gateway',
        'total_hourly': total_hourly,
        'total_monthly': total_monthly,
        'instances': details
    }