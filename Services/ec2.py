import boto3
import json
from typing import List, Dict, Any, Optional

class EC2PriceFetcher:
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

    def get_instance_price(self, instance_type: str, os: str = 'Linux') -> Optional[float]:
        try:
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.location},
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
            ]
            response = self.pricing_client.get_products(ServiceCode='AmazonEC2', Filters=filters)
            if not response['PriceList']: return None
            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            return float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
        except Exception as e:
            print(f"Error fetching EC2 price for {instance_type}: {e}")
            return None

    def get_ebs_price(self, volume_type: str = 'gp3') -> Optional[float]:
        cache_key = f"ebs-{volume_type}"
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        try:
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.location},
                {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
                {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': volume_type}
            ]
            response = self.pricing_client.get_products(ServiceCode='AmazonEC2', Filters=filters)

            if not response['PriceList']: 
                print(f"Warning: No EBS pricing data found for {volume_type} in {self.location}")
                return None

            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            price_per_gb_month = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            
            self._price_cache[cache_key] = price_per_gb_month
            return price_per_gb_month
        except Exception as e:
            print(f"Error fetching EBS price for {volume_type}: {e}")
            return None

def process_ec2(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    fetcher = EC2PriceFetcher(region)
    total_hourly = 0.0
    total_monthly = 0.0
    details = []

    for res in resources:
        if 'aws_instance' in res:
            for name, cfg in res['aws_instance'].items():
                itype = cfg.get('instance_type')
                ami = cfg.get('ami', '')
                
                # Basic OS detection
                os = 'Windows' if 'windows' in ami.lower() else 'Linux'

                instance_price_hr = fetcher.get_instance_price(itype, os) if itype else 0.0
                
                # Handle EBS volume cost (assuming root volume)
                # This is a simplification; a full implementation would parse ebs_block_device etc.
                root_volume_type = cfg.get('root_block_device', [{}])[0].get('volume_type', 'gp3')
                root_volume_size = cfg.get('root_block_device', [{}])[0].get('volume_size', 8) # Default to 8GB
                
                ebs_price_gb_mo = fetcher.get_ebs_price(root_volume_type) or 0.0
                ebs_monthly_cost = ebs_price_gb_mo * root_volume_size
                
                instance_monthly_cost = (instance_price_hr or 0.0) * 730
                total_instance_monthly = instance_monthly_cost + ebs_monthly_cost

                details.append({
                    'name': name,
                    'type': itype,
                    'os': os,
                    'storage_info': f"{root_volume_size}GB {root_volume_type}",
                    'price_per_hour': instance_price_hr,
                    'monthly_instance': instance_monthly_cost,
                    'monthly_storage': ebs_monthly_cost,
                    'monthly': total_instance_monthly
                })

                if instance_price_hr:
                    total_hourly += instance_price_hr
                total_monthly += total_instance_monthly

    return {
        'type': 'EC2',
        'total_hourly': total_hourly,
        'total_monthly': total_monthly,
        'instances': details
    }