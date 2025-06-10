import boto3
import json
from typing import List, Dict, Any, Optional

class RDSPriceFetcher:
    def __init__(self, region: str):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.region_mapping = {
            'us-west-2': 'US West (Oregon)', 'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)', 'us-west-1': 'US West (N. California)',
            'ca-central-1': 'Canada (Central)', 'eu-west-1': 'Europe (Ireland)',
            'eu-west-2': 'Europe (London)', 'eu-west-3': 'Europe (Paris)',
            'eu-central-1': 'Europe (Frankfurt)', 'eu-north-1': 'Europe (Stockholm)',
            'ap-southeast-1': 'Asia Pacific (Singapore)', 'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)', 'ap-northeast-2': 'Asia Pacific (Seoul)',
            'ap-south-1': 'Asia Pacific (Mumbai)', 'sa-east-1': 'South America (Sao Paulo)'
        }
        self.location = self.region_mapping.get(self.region)
        self.engine_mapping = {
            'mysql': 'MySQL', 'postgres': 'PostgreSQL', 'postgresql': 'PostgreSQL',
            'mariadb': 'MariaDB', 'oracle-ee': 'Oracle', 'sqlserver-se': 'SQL Server'
        }
        self._price_cache = {}

    def get_rds_instance_price(self, instance_class: str, engine: str, deployment_option: str) -> Optional[float]:
        try:
            if not self.location: return None
            engine_name = self.engine_mapping.get(engine.lower(), engine)
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_class},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.location},
                {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': engine_name},
                {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': deployment_option}
            ]
            response = self.pricing_client.get_products(ServiceCode='AmazonRDS', Filters=filters)
            if not response['PriceList']:
                 print(f"No pricing for RDS {instance_class} ({engine}/{deployment_option}) in {self.location}")
                 return None
            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            return float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
        except Exception as e:
            print(f"Error fetching RDS price for {instance_class}: {e}")
            return None
            
    def get_rds_storage_price(self, storage_type: str, deployment_option: str) -> Optional[float]:
        # Price is per GB-month
        cache_key = f"rds-storage-{storage_type}-{deployment_option}"
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        storage_mapping = {'gp2': 'General Purpose', 'gp3': 'General Purpose', 'io1': 'Provisioned IOPS'}
        aws_storage_type = storage_mapping.get(storage_type, 'General Purpose')

        try:
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.location},
                {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Database Storage'},
                {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': deployment_option},
                {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': aws_storage_type},
            ]
            response = self.pricing_client.get_products(ServiceCode='AmazonRDS', Filters=filters)
            if not response['PriceList']: return None
            price_item = json.loads(response['PriceList'][0])
            terms = price_item['terms']['OnDemand']
            price_dimensions = list(terms.values())[0]['priceDimensions']
            price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            self._price_cache[cache_key] = price
            return price
        except Exception as e:
            print(f"Error fetching RDS storage price for {storage_type}: {e}")
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
                storage_size = cfg.get('allocated_storage', 20)
                storage_type = cfg.get('storage_type', 'gp2')
                
                deployment_option = 'Multi-AZ' if multi_az else 'Single-AZ'
                
                price_hr = fetcher.get_rds_instance_price(instance_class, engine, deployment_option) if instance_class else 0.0
                storage_price_gb_mo = fetcher.get_rds_storage_price(storage_type, deployment_option) or 0.0

                monthly_instance = (price_hr or 0.0) * 730
                monthly_storage = storage_price_gb_mo * storage_size
                total_instance_monthly = monthly_instance + monthly_storage
                
                details.append({
                    'name': name,
                    'type': instance_class,
                    'engine': engine,
                    'multi_az': multi_az,
                    'storage_info': f"{storage_size}GB {storage_type}",
                    'price_per_hour': price_hr,
                    'monthly_instance': monthly_instance,
                    'monthly_storage': monthly_storage,
                    'monthly': total_instance_monthly
                })

                if price_hr:
                    total_hourly += price_hr
                total_monthly += total_instance_monthly

    return {
        'type': 'RDS',
        'total_hourly': total_hourly,
        'total_monthly': total_monthly,
        'instances': details
    }