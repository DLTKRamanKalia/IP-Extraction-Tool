import ipaddress
from azure.identity import ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.subscription import SubscriptionClient
from config import config


class AzureService:
    def __init__(self):
        """Initialize Azure service with credentials from config"""
        try:
            credentials = config.get_azure_credentials()
            self.tenant_id = credentials['tenant_id']
            self.client_id = credentials['client_id']
            self.client_secret = credentials['client_secret']
            self.subscription_id = credentials['subscription_id']
            self.credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        except Exception as e:
            raise Exception(f"Failed to load Azure credentials: {str(e)}")

    def get_all_regions(self):
        """Get list of all Azure regions available for the subscription"""
        try:
            subscription_client = SubscriptionClient(self.credential)
            locations = subscription_client.subscriptions.list_locations(self.subscription_id)
            return [loc.name for loc in locations]
        except Exception as e:
            raise Exception(f"Failed to retrieve Azure regions: {str(e)}")

    def _find_parent_cidr(self, subnet_cidr, vnet_cidrs):
        """Return the VNet CIDR that contains this subnet, or the first CIDR."""
        try:
            subnet_net = ipaddress.ip_network(subnet_cidr, strict=False)
            for cidr in vnet_cidrs:
                try:
                    if subnet_net.subnet_of(ipaddress.ip_network(cidr, strict=False)):
                        return cidr
                except (ValueError, TypeError):
                    continue
        except (ValueError, TypeError):
            pass
        return vnet_cidrs[0] if vnet_cidrs else ''

    def get_vnet_and_subnet_info(self, network_client):
        """Get all VNets and Subnets across the subscription"""
        results = []
        regions_seen = set()

        try:
            vnets = network_client.virtual_networks.list_all()

            for vnet in vnets:
                vnet_id = vnet.id
                vnet_name = vnet.name
                region = vnet.location
                regions_seen.add(region)

                # Collect all address prefixes (primary + any secondaries)
                vnet_cidrs = list(vnet.address_space.address_prefixes) \
                    if vnet.address_space and vnet.address_space.address_prefixes \
                    else []
                vnet_all_cidrs = ', '.join(vnet_cidrs)

                subnets = vnet.subnets or []

                if subnets:
                    for subnet in subnets:
                        # Prefer address_prefix; fall back to first entry of address_prefixes
                        subnet_cidr = subnet.address_prefix or (
                            (subnet.address_prefixes or [''])[0]
                        )

                        # Identify which VNet CIDR this subnet belongs to
                        parent_cidr = self._find_parent_cidr(subnet_cidr, vnet_cidrs) \
                            if vnet_cidrs else ''

                        # ip_configurations holds one entry per assigned IP
                        used_ips = len(subnet.ip_configurations or [])

                        results.append({
                            'region': region,
                            'vpc_id': vnet_id,
                            'vpc_name': vnet_name,
                            'vpc_cidr': parent_cidr,
                            'vpc_all_cidrs': vnet_all_cidrs,
                            'subnet_id': subnet.id,
                            'subnet_name': subnet.name,
                            'subnet_cidr': subnet_cidr,
                            'used_ips': used_ips
                        })
                else:
                    results.append({
                        'region': region,
                        'vpc_id': vnet_id,
                        'vpc_name': vnet_name,
                        'vpc_cidr': vnet_cidrs[0] if vnet_cidrs else '',
                        'vpc_all_cidrs': vnet_all_cidrs,
                        'subnet_id': '',
                        'subnet_name': '',
                        'subnet_cidr': '',
                        'used_ips': 0
                    })

        except Exception as e:
            print(f"Error retrieving VNet/Subnet info: {str(e)}")

        return results, regions_seen

    def scan_all_regions(self):
        """Scan Azure subscription for all VNet and Subnet information"""
        try:
            network_client = NetworkManagementClient(self.credential, self.subscription_id)
            all_results, regions_seen = self.get_vnet_and_subnet_info(network_client)

            print(f"Azure scan complete. Found {len(all_results)} entries across {len(regions_seen)} regions.")

            return {
                'success': True,
                'data': all_results,
                'total_entries': len(all_results),
                'regions_scanned': len(regions_seen)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
