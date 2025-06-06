import os
from parser import parse_terraform_config
from Services import ec2
from Services.rds import process_rds

service_map = {
    'aws_instance': ec2.process_ec2,
    'aws_db_instance': process_rds
}

def main():
    tf_file = os.path.join(os.path.dirname(__file__), 'Terraform', 'main.tf')
    region, resources = parse_terraform_config(tf_file)

    if not region or not resources:
        print("Error: Region or resources not found.")
        return

    print(f"Detected Region: {region}\n")

    results = []
    for service_key, handler in service_map.items():
        filtered = [r for r in resources if service_key in r]
        if filtered:
            result = handler(region, filtered)
            results.append(result)

    total_hourly = sum(r['total_hourly'] for r in results)
    total_monthly = sum(r['total_monthly'] for r in results)

    print("\n======== COST SUMMARY ========")
    for r in results:
        print(f"\n--- {r['type']} Instances ---")
        for inst in r['instances']:
            if r['type'] == 'RDS':
                multi_az_text = " (Multi-AZ)" if inst.get('multi_az') else ""
                print(f"{inst['name']} | {inst['type']} | {inst['engine']}{multi_az_text} | ${inst['price_per_hour']:.4f}/hr | ${inst['monthly']:.2f}/mo")
            else:
                print(f"{inst['name']} | {inst['type']} | ${inst['price_per_hour']:.4f}/hr | ${inst['monthly']:.2f}/mo")
    print("\nTOTAL HOURLY COST: ${:.4f}".format(total_hourly))
    print("TOTAL MONTHLY COST: ${:.2f}".format(total_monthly))

if __name__ == "__main__":
    main()
