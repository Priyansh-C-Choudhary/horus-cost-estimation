"""
Security Groups Service Cost Calculator
Security Groups are free in AWS, but we track them for infrastructure overview
"""

from typing import List, Dict, Any

def process_security_group(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Security Group resources - Security Groups are free in AWS
    
    Args:
        region: AWS region
        resources: List of Security Group resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_security_group' in res:
            for name, cfg in res['aws_security_group'].items():
                vpc_id = cfg.get('vpc_id', 'N/A')
                description = cfg.get('description', 'No description')
                
                # Count ingress and egress rules
                ingress_rules = cfg.get('ingress', [])
                egress_rules = cfg.get('egress', [])
                
                ingress_count = len(ingress_rules) if isinstance(ingress_rules, list) else 0
                egress_count = len(egress_rules) if isinstance(egress_rules, list) else 0
                
                # Analyze rule complexity
                total_rules = ingress_count + egress_count
                
                details.append({
                    'name': name,
                    'type': f'Security Group ({total_rules} rules)',
                    'description': description[:50] + '...' if len(description) > 50 else description,
                    'vpc_id': vpc_id,
                    'ingress_rules': ingress_count,
                    'egress_rules': egress_count,
                    'total_rules': total_rules,
                    'price_per_hour': 0.0,  # Security Groups are free
                    'monthly': 0.0
                })
    
    return {
        'type': 'Security Group',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

def process_security_group_rule(region: str, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process Security Group Rule resources - Individual rules are also free
    
    Args:
        region: AWS region
        resources: List of Security Group Rule resources
        
    Returns:
        Dictionary with cost information
    """
    details = []
    
    for res in resources:
        if 'aws_security_group_rule' in res:
            for name, cfg in res['aws_security_group_rule'].items():
                rule_type = cfg.get('type', 'N/A')  # ingress or egress
                protocol = cfg.get('protocol', 'N/A')
                from_port = cfg.get('from_port', 'N/A')
                to_port = cfg.get('to_port', 'N/A')
                security_group_id = cfg.get('security_group_id', 'N/A')
                
                # Determine source/destination
                cidr_blocks = cfg.get('cidr_blocks', [])
                source_security_group_id = cfg.get('source_security_group_id')
                
                if cidr_blocks:
                    source_dest = f"CIDR: {', '.join(cidr_blocks)}"
                elif source_security_group_id:
                    source_dest = f"SG: {source_security_group_id}"
                else:
                    source_dest = "Other"
                
                port_range = f"{from_port}-{to_port}" if from_port != to_port else str(from_port)
                
                details.append({
                    'name': name,
                    'type': f'{rule_type.title()} Rule ({protocol}:{port_range})',
                    'rule_type': rule_type,
                    'protocol': protocol,
                    'port_range': port_range,
                    'source_destination': source_dest,
                    'security_group_id': security_group_id,
                    'price_per_hour': 0.0,  # Security Group Rules are free
                    'monthly': 0.0
                })
    
    return {
        'type': 'Security Group Rule',
        'total_hourly': 0.0,
        'total_monthly': 0.0,
        'instances': details
    }

def analyze_security_group_complexity(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze Security Group configuration complexity
    This doesn't affect cost but provides insights into infrastructure complexity
    
    Args:
        resources: List of Security Group resources
        
    Returns:
        Dictionary with complexity analysis
    """
    analysis = {
        'total_security_groups': 0,
        'total_rules': 0,
        'avg_rules_per_sg': 0,
        'max_rules_in_sg': 0,
        'sgs_with_many_rules': 0,  # > 20 rules
        'complexity_score': 'Low'
    }
    
    rule_counts = []
    
    for res in resources:
        if 'aws_security_group' in res:
            for name, cfg in res['aws_security_group'].items():
                analysis['total_security_groups'] += 1
                
                ingress_rules = cfg.get('ingress', [])
                egress_rules = cfg.get('egress', [])
                
                ingress_count = len(ingress_rules) if isinstance(ingress_rules, list) else 0
                egress_count = len(egress_rules) if isinstance(egress_rules, list) else 0
                
                total_rules = ingress_count + egress_count
                rule_counts.append(total_rules)
                analysis['total_rules'] += total_rules
                
                if total_rules > 20:
                    analysis['sgs_with_many_rules'] += 1
    
    if rule_counts:
        analysis['avg_rules_per_sg'] = sum(rule_counts) / len(rule_counts)
        analysis['max_rules_in_sg'] = max(rule_counts)
        
        # Determine complexity score
        if analysis['avg_rules_per_sg'] > 15 or analysis['sgs_with_many_rules'] > 2:
            analysis['complexity_score'] = 'High'
        elif analysis['avg_rules_per_sg'] > 8 or analysis['sgs_with_many_rules'] > 0:
            analysis['complexity_score'] = 'Medium'
        else:
            analysis['complexity_score'] = 'Low'
    
    return analysis

# Utility function to check for common security group misconfigurations
def check_security_group_best_practices(resources: List[Dict[str, Any]]) -> List[str]:
    """
    Check for common security group misconfigurations
    
    Args:
        resources: List of Security Group resources
        
    Returns:
        List of warnings/recommendations
    """
    warnings = []
    
    for res in resources:
        if 'aws_security_group' in res:
            for name, cfg in res['aws_security_group'].items():
                ingress_rules = cfg.get('ingress', [])
                
                if isinstance(ingress_rules, list):
                    for rule in ingress_rules:
                        # Check for overly permissive rules
                        cidr_blocks = rule.get('cidr_blocks', [])
                        if '0.0.0.0/0' in cidr_blocks:
                            from_port = rule.get('from_port')
                            to_port = rule.get('to_port')
                            protocol = rule.get('protocol')
                            
                            if protocol == 'tcp' and from_port == 22:
                                warnings.append(f"Security Group '{name}': SSH (port 22) open to 0.0.0.0/0")
                            elif protocol == 'tcp' and from_port == 3389:
                                warnings.append(f"Security Group '{name}': RDP (port 3389) open to 0.0.0.0/0")
                            elif from_port == 0 and to_port == 65535:
                                warnings.append(f"Security Group '{name}': All ports open to 0.0.0.0/0")
    
    return warnings