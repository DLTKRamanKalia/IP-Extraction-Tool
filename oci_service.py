import ipaddress
import oci
from config import config


class OCIService:
    def __init__(self):
        """Initialize OCI service with credentials from config"""
        try:
            credentials = config.get_oci_credentials()
            self.config_dict = {
                'user': credentials['user_ocid'],
                'key_file': credentials['key_file'],
                'fingerprint': credentials['fingerprint'],
                'tenancy': credentials['tenancy_ocid'],
                'region': credentials['region']
            }
            self.tenancy_id = credentials['tenancy_ocid']
            oci.config.validate_config(self.config_dict)
        except Exception as e:
            raise Exception(f"Failed to load OCI credentials: {str(e)}")

    def get_all_regions(self):
        """Get list of all OCI regions subscribed to"""
        try:
            identity_client = oci.identity.IdentityClient(self.config_dict)
            regions = identity_client.list_region_subscriptions(self.tenancy_id).data
            return [r.region_name for r in regions]
        except Exception as e:
            raise Exception(f"Failed to retrieve OCI regions: {str(e)}")

    def _find_parent_cidr(self, subnet_cidr, vcn_cidrs):
        """Return the VCN CIDR that contains this subnet, or the first CIDR."""
        try:
            subnet_net = ipaddress.ip_network(subnet_cidr, strict=False)
            for cidr in vcn_cidrs:
                try:
                    if subnet_net.subnet_of(ipaddress.ip_network(cidr, strict=False)):
                        return cidr
                except (ValueError, TypeError):
                    continue
        except (ValueError, TypeError):
            pass
        return vcn_cidrs[0] if vcn_cidrs else ''

    def get_vcn_and_subnet_info(self, region):
        """Get VCN and Subnet information for a specific OCI region"""
        results = []

        try:
            region_config = dict(self.config_dict)
            region_config['region'] = region

            identity_client = oci.identity.IdentityClient(region_config)
            network_client = oci.core.VirtualNetworkClient(region_config)

            # List all compartments under the tenancy
            compartments = oci.pagination.list_call_get_all_results(
                identity_client.list_compartments,
                self.tenancy_id,
                compartment_id_in_subtree=True,
                lifecycle_state='ACTIVE'
            ).data

            # Include root compartment (tenancy itself)
            compartment_ids = [self.tenancy_id] + [c.id for c in compartments]

            for compartment_id in compartment_ids:
                try:
                    vcns = oci.pagination.list_call_get_all_results(
                        network_client.list_vcns,
                        compartment_id
                    ).data

                    for vcn in vcns:
                        vcn_id = vcn.id
                        vcn_name = vcn.display_name

                        # cidr_blocks is the modern multi-CIDR list; fall back to
                        # the legacy cidr_block field if it is absent or empty
                        vcn_cidrs = list(vcn.cidr_blocks) \
                            if vcn.cidr_blocks \
                            else ([vcn.cidr_block] if vcn.cidr_block else [])
                        vcn_all_cidrs = ', '.join(vcn_cidrs)

                        subnets = oci.pagination.list_call_get_all_results(
                            network_client.list_subnets,
                            compartment_id,
                            vcn_id=vcn_id
                        ).data

                        if subnets:
                            for subnet in subnets:
                                subnet_cidr = subnet.cidr_block or ''
                                parent_cidr = self._find_parent_cidr(subnet_cidr, vcn_cidrs)

                                # Count private IPs assigned in this subnet
                                try:
                                    private_ips = oci.pagination.list_call_get_all_results(
                                        network_client.list_private_ips,
                                        subnet_id=subnet.id
                                    ).data
                                    used_ips = len(private_ips)
                                except Exception:
                                    used_ips = 0

                                results.append({
                                    'region': region,
                                    'vpc_id': vcn_id,
                                    'vpc_name': vcn_name,
                                    'vpc_cidr': parent_cidr,
                                    'vpc_all_cidrs': vcn_all_cidrs,
                                    'subnet_id': subnet.id,
                                    'subnet_name': subnet.display_name,
                                    'subnet_cidr': subnet_cidr,
                                    'used_ips': used_ips
                                })
                        else:
                            results.append({
                                'region': region,
                                'vpc_id': vcn_id,
                                'vpc_name': vcn_name,
                                'vpc_cidr': vcn_cidrs[0] if vcn_cidrs else '',
                                'vpc_all_cidrs': vcn_all_cidrs,
                                'subnet_id': '',
                                'subnet_name': '',
                                'subnet_cidr': '',
                                'used_ips': 0
                            })

                except Exception as e:
                    print(f"Error scanning compartment {compartment_id} in {region}: {str(e)}")

        except Exception as e:
            print(f"Error in OCI region {region}: {str(e)}")

        return results

    def scan_all_regions(self):
        """Scan all OCI regions and collect VCN/Subnet information"""
        all_results = []

        try:
            regions = self.get_all_regions()
            print(f"Scanning {len(regions)} OCI regions...")

            for region in regions:
                print(f"Scanning OCI region: {region}")
                region_results = self.get_vcn_and_subnet_info(region)
                all_results.extend(region_results)

            return {
                'success': True,
                'data': all_results,
                'total_entries': len(all_results),
                'regions_scanned': len(regions)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
