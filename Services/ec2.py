import boto3
import json
from typing import List, Dict, Any, Optional

class EC2PriceFetcher:
    def __init__(self, region: str):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'ca-central-1': 'Canada (Central)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-west-2': 'Europe (London)',
            'eu-west-3': 'Europe (Paris)',
            'eu-central-1': 'Europe (Frankfurt)',
            'eu-north-1': 'Europe (Stockholm)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'ap-northeast-2': 'Asia Pacific (Seoul)',
            'ap-south-1': 'Asia Pacific (Mumbai)',
            'sa-east-1': 'South America (Sao Paulo)'
        }

    def get_instance_price(self, instance_type: str, os: str = 'Linux') -> Optional[float]:
        try:
            location = self.region_mapping.get(self.region, self.region)
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
                ]
            )

            if not response['PriceList']:
                print(f"No pricing data for {instance_type} in {location}")
                return None

            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            price_per_hour = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])

            return price_per_hour

        except Exception as e:
            print(f"Error fetching price for {instance_type}: {str(e)}")
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
                price = fetcher.get_instance_price(itype) if itype else None
                monthly = price * 730 if price else 0

                details.append({
                    'name': name,
                    'type': itype,
                    'price_per_hour': price,
                    'monthly': monthly
                })

                if price:
                    total_hourly += price
                    total_monthly += monthly

    return {
        'type': 'EC2',
        'total_hourly': total_hourly,
        'total_monthly': total_monthly,
        'instances': details
    }
