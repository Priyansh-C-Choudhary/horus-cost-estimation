import boto3
import json
from typing import List, Dict, Any, Optional

class RDSPriceFetcher:
    def __init__(self, region: str):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.region_mapping = {
            'us-west-2': 'US West (Oregon)',
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
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
            'sa-east-1': 'South America (Sao Paulo)',
        }

    def get_rds_instance_price(self, instance_class: str, engine: str = 'MySQL', deployment_option: str = 'Single-AZ') -> Optional[float]:
        try:
            location = self.region_mapping.get(self.region)
            if not location:
                print(f"Warning: Region {self.region} not supported for RDS pricing lookup")
                return None

            # Map common engine names to AWS pricing engine names
            engine_mapping = {
                'mysql': 'MySQL',
                'postgres': 'PostgreSQL',
                'postgresql': 'PostgreSQL',
                'mariadb': 'MariaDB',
                'oracle-ee': 'Oracle',
                'oracle-se2': 'Oracle',
                'oracle-se1': 'Oracle',
                'oracle-se': 'Oracle',
                'sqlserver-ee': 'SQL Server',
                'sqlserver-se': 'SQL Server',
                'sqlserver-ex': 'SQL Server',
                'sqlserver-web': 'SQL Server'
            }
            
            engine_name = engine_mapping.get(engine.lower(), engine)

            response = self.pricing_client.get_products(
                ServiceCode='AmazonRDS',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_class},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                    {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': engine_name},
                    {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': deployment_option}
                ]
            )

            if not response['PriceList']:
                print(f"No pricing data for RDS {instance_class} ({engine}) in {location}")
                return None

            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            price_per_hour = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])

            return price_per_hour

        except Exception as e:
            print(f"Error fetching RDS price for {instance_class}: {str(e)}")
            return None

def process_rds(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    fetcher = RDSPriceFetcher(region)
    total_hourly = 0.0
    total_monthly = 0.0
    details = []

    for res in resources:
        if 'aws_db_instance' in res:
            for name, cfg in res['aws_db_instance'].items():
                instance_class = cfg.get('instance_class')
                engine = cfg.get('engine', 'mysql')
                multi_az = cfg.get('multi_az', False)
                
                # Determine deployment option
                deployment_option = 'Multi-AZ' if multi_az else 'Single-AZ'
                
                price = fetcher.get_rds_instance_price(instance_class, engine, deployment_option) if instance_class else None
                monthly = price * 730 if price else 0

                details.append({
                    'name': name,
                    'type': instance_class,
                    'engine': engine,
                    'multi_az': multi_az,
                    'price_per_hour': price,
                    'monthly': monthly
                })

                if price:
                    total_hourly += price
                    total_monthly += monthly

    return {
        'type': 'RDS',
        'total_hourly': total_hourly,
        'total_monthly': total_monthly,
        'instances': details
    }