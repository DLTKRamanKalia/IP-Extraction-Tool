import ipaddress
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import config

class AWSService:
    def __init__(self, account=None):
        """Initialize AWS service with credentials from config"""
        try:
            if account:
                credentials = config.get_aws_credentials_for_account(account)
            else:
                credentials = config.get_aws_credentials()
            self.access_key = credentials['access_key_id']
            self.secret_key = credentials['secret_access_key']
        except Exception as e:
            raise Exception(f"Failed to load AWS credentials: {str(e)}")

    def _get_ec2_client(self, region):
        """Create EC2 client for specific region"""
        return boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )

    def get_all_regions(self):
        """Get list of all AWS regions"""
        try:
            ec2_client = self._get_ec2_client('us-east-1')
            regions = ec2_client.describe_regions()
            return [region['RegionName'] for region in regions['Regions']]
        except Exception as e:
            raise Exception(f"Failed to retrieve AWS regions: {str(e)}")

    def _get_tag_value(self, tags, key='Name'):
        """Extract tag value from AWS resource tags"""
        if tags:
            for tag in tags:
                if tag['Key'] == key:
                    return tag['Value']
        return ''

    def _get_vpc_cidrs(self, vpc):
        """Return all associated IPv4 CIDRs for a VPC, falling back to primary."""
        assocs = vpc.get('CidrBlockAssociationSet', [])
        cidrs = [
            a['CidrBlock'] for a in assocs
            if a.get('CidrBlockState', {}).get('State') == 'associated'
        ]
        return cidrs if cidrs else [vpc['CidrBlock']]

    def _find_parent_cidr(self, subnet_cidr, vpc_cidrs):
        """Return the VPC CIDR that contains this subnet, or the first CIDR."""
        subnet_net = ipaddress.IPv4Network(subnet_cidr)
        for cidr in vpc_cidrs:
            try:
                if subnet_net.subnet_of(ipaddress.IPv4Network(cidr)):
                    return cidr
            except (ValueError, TypeError):
                continue
        return vpc_cidrs[0]

    def get_vpc_and_subnet_info(self, region):
        """Get VPC and Subnet information for a specific region"""
        results = []

        try:
            ec2_client = self._get_ec2_client(region)

            # Get all VPCs in the region
            vpcs_response = ec2_client.describe_vpcs()
            vpcs = vpcs_response.get('Vpcs', [])

            for vpc in vpcs:
                vpc_id = vpc['VpcId']
                vpc_name = self._get_tag_value(vpc.get('Tags', []))

                # Collect every associated CIDR block (primary + secondaries)
                vpc_cidrs = self._get_vpc_cidrs(vpc)
                vpc_all_cidrs = ', '.join(vpc_cidrs)

                # Get all subnets for this VPC
                subnets_response = ec2_client.describe_subnets(
                    Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
                )
                subnets = subnets_response.get('Subnets', [])

                if subnets:
                    for subnet in subnets:
                        subnet_id = subnet['SubnetId']
                        subnet_name = self._get_tag_value(subnet.get('Tags', []))
                        subnet_cidr = subnet['CidrBlock']

                        # Identify which VPC CIDR this subnet belongs to
                        parent_cidr = self._find_parent_cidr(subnet_cidr, vpc_cidrs)

                        # Calculate used IPs:
                        # total IPs in CIDR - 5 AWS-reserved - available
                        network = ipaddress.IPv4Network(subnet_cidr)
                        aws_reserved = 5 if network.prefixlen < 31 else 0
                        available = subnet.get('AvailableIpAddressCount', 0)
                        used_ips = network.num_addresses - aws_reserved - available

                        results.append({
                            'region': region,
                            'vpc_id': vpc_id,
                            'vpc_name': vpc_name,
                            'vpc_cidr': parent_cidr,
                            'vpc_all_cidrs': vpc_all_cidrs,
                            'subnet_id': subnet_id,
                            'subnet_name': subnet_name,
                            'subnet_cidr': subnet_cidr,
                            'used_ips': used_ips
                        })
                else:
                    # VPC with no subnets
                    results.append({
                        'region': region,
                        'vpc_id': vpc_id,
                        'vpc_name': vpc_name,
                        'vpc_cidr': vpc_cidrs[0],
                        'vpc_all_cidrs': vpc_all_cidrs,
                        'subnet_id': '',
                        'subnet_name': '',
                        'subnet_cidr': '',
                        'used_ips': 0
                    })

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UnauthorizedOperation':
                print(f"Skipping region {region}: Unauthorized")
            else:
                print(f"Error in region {region}: {str(e)}")
        except Exception as e:
            print(f"Error in region {region}: {str(e)}")

        return results

    def scan_all_regions(self, region=None):
        """Scan one or all AWS regions and collect VPC/Subnet information.

        Args:
            region: None or "all" → scan every region;
                    a region code (e.g. "us-east-1") → scan only that region.
        """
        all_results = []

        try:
            if region and region != 'all':
                regions = [region]
            else:
                regions = self.get_all_regions()

            print(f"Scanning {len(regions)} AWS region(s)...")

            for r in regions:
                print(f"Scanning region: {r}")
                region_results = self.get_vpc_and_subnet_info(r)
                all_results.extend(region_results)

            return {
                'success': True,
                'data': all_results,
                'total_entries': len(all_results),
                'regions_scanned': len(regions)
            }

        except NoCredentialsError:
            return {
                'success': False,
                'error': 'AWS credentials not found or invalid'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
