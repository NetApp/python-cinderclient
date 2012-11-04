# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import httplib2
import urlparse

from cinderclient import client as base_client
from cinderclient.v1 import client
from tests import fakes


def _stub_volume(**kwargs):
    volume = {
        'id': '1234',
        'display_name': None,
        'display_description': None,
        "attachments": [],
        "availability_zone": "cinder",
        "created_at": "2012-08-27T00:00:00.000000",
        "display_description": None,
        "display_name": None,
        "id": '00000000-0000-0000-0000-000000000000',
        "metadata": {},
        "size": 1,
        "snapshot_id": None,
        "status": "available",
        "volume_type": "None",
    }
    volume.update(kwargs)
    return volume


def _stub_snapshot(**kwargs):
    snapshot = {
        "created_at": "2012-08-28T16:30:31.000000",
        "display_description": None,
        "display_name": None,
        "id": '11111111-1111-1111-1111-111111111111',
        "size": 1,
        "status": "available",
        "volume_id": '00000000-0000-0000-0000-000000000000',
    }
    snapshot.update(kwargs)
    return snapshot


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url')
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(base_client.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.callstack = []

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            assert 'body' in kwargs

        # Call the method
        args = urlparse.parse_qsl(urlparse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))

        status, body = getattr(self, callback)(**kwargs)
        if hasattr(status, 'items'):
            return httplib2.Response(status), body
        else:
            return httplib2.Response({"status": status}), body

    #
    # Snapshots
    #

    def get_snapshots_detail(self, **kw):
        return (200, {'snapshots': [
            _stub_snapshot(),
        ]})

    def get_snapshots_1234(self, **kw):
        return (200, {'snapshot': _stub_snapshot(id='1234')})

    def put_snapshots_1234(self, **kw):
        snapshot = _stub_snapshot(id='1234')
        snapshot.update(kw['body']['snapshot'])
        return (200, {'snapshot': snapshot})

    #
    # Volumes
    #

    def put_volumes_1234(self, **kw):
        volume = _stub_volume(id='1234')
        volume.update(kw['body']['volume'])
        return (200, {'volume': volume})

    def get_volumes(self, **kw):
        return (200, {"volumes": [
            {'id': 1234, 'name': 'sample-volume'},
            {'id': 5678, 'name': 'sample-volume2'}
        ]})

    # TODO(jdg): This will need to change
    # at the very least it's not complete
    def get_volumes_detail(self, **kw):
        return (200, {"volumes": [
            {'id': 1234,
             'name': 'sample-volume',
             'attachments': [{'server_id': 1234}]},
        ]})

    def get_volumes_1234(self, **kw):
        r = {'volume': self.get_volumes_detail()[1]['volumes'][0]}
        return (200, r)

    def post_volumes_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(body.keys()) == 1
        action = body.keys()[0]
        if action == 'os-attach':
            assert body[action].keys() == ['instance_uuid', 'mountpoint']
        elif action == 'os-detach':
            assert body[action] is None
        elif action == 'os-reserve':
            assert body[action] is None
        elif action == 'os-unreserve':
            assert body[action] is None
        elif action == 'os-initialize_connection':
            assert body[action].keys() == ['connector']
            return (202, {'connection_info': 'foos'})
        elif action == 'os-terminate_connection':
            assert body[action].keys() == ['connector']
        elif action == 'os-begin_detaching':
            assert body[action] is None
        elif action == 'os-roll_detaching':
            assert body[action] is None
        else:
            raise AssertionError("Unexpected server action: %s" % action)
        return (resp, _body)

    def get_shares_1234(self, **kw):
        share = {'share': {'id': 1234, 'name': 'sample-volume'}}
        return (200, share)

    def get_shares_detail(self):
        shares = {'shares': [
                    {'id': 1234,
                     'name': 'sharename',
                     'attachments': [{'server_id': 111}]
                     }]}
        return (200, shares)

    def post_shares_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(body.keys()) == 1
        action = body.keys()[0]
        if action == 'os-access_allow':
            assert body[action].keys() == ['access_type', 'access_to']
        elif action == 'os-access_deny':
            assert body[action].keys() == ['access_id']
        elif action == 'os-access_list':
            assert body[action] == None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, _body)

    def get_volumes_1234(self, **kw):
        r = {'volume': self.get_volumes_detail()[1]['volumes'][0]}
        return (200, r)

    def post_servers(self, body, **kw):
        assert set(body.keys()) <= set(['server', 'os:scheduler_hints'])
        fakes.assert_has_keys(body['server'],
                              required=['name', 'imageRef', 'flavorRef'],
                              optional=['metadata', 'personality'])
        if 'personality' in body['server']:
            for pfile in body['server']['personality']:
                fakes.assert_has_keys(pfile, required=['path', 'contents'])
        return (202, self.get_servers_1234()[1])

    def get_servers_1234(self, **kw):
        r = {'server': self.get_servers_detail()[1]['servers'][0]}
        return (200, r)

    def get_servers_5678(self, **kw):
        r = {'server': self.get_servers_detail()[1]['servers'][1]}
        return (200, r)

    def put_servers_1234(self, body, **kw):
        assert body.keys() == ['server']
        fakes.assert_has_keys(body['server'], optional=['name', 'adminPass'])
        return (204, None)

    def post_shares(self, **kwargs):
        return (202, {'share': {}})

    def post_volumes(self, **kw):
        return (202, {'volume': {}})

    def delete_volumes_1234(self, **kw):
        return (202, None)

    def delete_shares_1234(self, **kw):
        return (202, None)

    def delete_servers_1234_metadata_test_key(self, **kw):
        return (204, None)

    def delete_servers_1234_metadata_key1(self, **kw):
        return (204, None)

    def delete_servers_1234_metadata_key2(self, **kw):
        return (204, None)

    def post_servers_1234_metadata(self, **kw):
        return (204, {'metadata': {'test_key': 'test_value'}})

    def get_servers_1234_diagnostics(self, **kw):
        return (200, {'data': 'Fake diagnostics'})

    def get_servers_1234_actions(self, **kw):
        return (
            200, {'actions': [
                {
                    'action': 'rebuild',
                    'error': None,
                    'created_at': '2011-12-30 11:45:36'
                },
                {
                    'action': 'reboot',
                    'error': 'Failed!',
                    'created_at': '2011-12-30 11:40:29'
                },
            ]})

    #
    # Server Addresses
    #

    def get_servers_1234_ips(self, **kw):
        return (200, {'addresses':
                      self.get_servers_1234()[1]['server']['addresses']})

    def get_servers_1234_ips_public(self, **kw):
        return (200, {'public':
                      self.get_servers_1234_ips()[1]['addresses']['public']})

    def get_servers_1234_ips_private(self, **kw):
        return (200, {'private':
                      self.get_servers_1234_ips()[1]['addresses']['private']})

    def delete_servers_1234_ips_public_1_2_3_4(self, **kw):
        return (202, None)

    #
    # Server actions
    #

    def post_servers_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(body.keys()) == 1
        action = body.keys()[0]
        if action == 'reboot':
            assert body[action].keys() == ['type']
            assert body[action]['type'] in ['HARD', 'SOFT']
        elif action == 'rebuild':
            keys = body[action].keys()
            if 'adminPass' in keys:
                keys.remove('adminPass')
            assert keys == ['imageRef']
            _body = self.get_servers_1234()[1]
        elif action == 'resize':
            assert body[action].keys() == ['flavorRef']
        elif action == 'confirmResize':
            assert body[action] is None
            # This one method returns a different response code
            return (204, None)
        elif action == 'revertResize':
            assert body[action] is None
        elif action == 'migrate':
            assert body[action] is None
        elif action == 'rescue':
            assert body[action] is None
        elif action == 'unrescue':
            assert body[action] is None
        elif action == 'lock':
            assert body[action] is None
        elif action == 'unlock':
            assert body[action] is None
        elif action == 'addFixedIp':
            assert body[action].keys() == ['networkId']
        elif action == 'removeFixedIp':
            assert body[action].keys() == ['address']
        elif action == 'addFloatingIp':
            assert body[action].keys() == ['address']
        elif action == 'removeFloatingIp':
            assert body[action].keys() == ['address']
        elif action == 'createImage':
            assert set(body[action].keys()) == set(['name', 'metadata'])
            resp = dict(status=202, location="http://blah/images/456")
        elif action == 'changePassword':
            assert body[action].keys() == ['adminPass']
        elif action == 'os-getConsoleOutput':
            assert body[action].keys() == ['length']
            return (202, {'output': 'foo'})
        elif action == 'os-getVNCConsole':
            assert body[action].keys() == ['type']
        elif action == 'os-migrateLive':
            assert set(body[action].keys()) == set(['host',
                                                    'block_migration',
                                                    'disk_over_commit'])
        else:
            raise AssertionError("Unexpected server action: %s" % action)
        return (resp, _body)

    #
    # Cloudpipe
    #

    def get_os_cloudpipe(self, **kw):
        return (200, {'cloudpipes': [
            {'project_id':1}
        ]})

    def post_os_cloudpipe(self, **ks):
        return (202, {'instance_id': '9d5824aa-20e6-4b9f-b967-76a699fc51fd'})

    #
    # Flavors
    #

    def get_flavors(self, **kw):
        return (200, {'flavors': [
            {'id': 1, 'name': '256 MB Server'},
            {'id': 2, 'name': '512 MB Server'}
        ]})

    def get_flavors_detail(self, **kw):
        return (200, {'flavors': [
            {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10,
             'OS-FLV-EXT-DATA:ephemeral': 10},
            {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20,
             'OS-FLV-EXT-DATA:ephemeral': 20}
        ]})

    def get_flavors_1(self, **kw):
        return (200, {'flavor': self.get_flavors_detail()[1]['flavors'][0]})

    def get_flavors_2(self, **kw):
        return (200, {'flavor': self.get_flavors_detail()[1]['flavors'][1]})

    def get_flavors_3(self, **kw):
        # Diablo has no ephemeral
        return (200, {'flavor': {'id': 3, 'name': '256 MB Server',
                                 'ram': 256, 'disk': 10}})

    def delete_flavors_flavordelete(self, **kw):
        return (202, None)

    def post_flavors(self, body, **kw):
        return (202, {'flavor': self.get_flavors_detail()[1]['flavors'][0]})

    #
    # Floating ips
    #

    def get_os_floating_ip_pools(self):
        return (200, {'floating_ip_pools': [{'name': 'foo', 'name': 'bar'}]})

    def get_os_floating_ips(self, **kw):
        return (200, {'floating_ips': [
            {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
            {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'},
        ]})

    def get_os_floating_ips_1(self, **kw):
        return (200, {'floating_ip':
                {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'}
                })

    def post_os_floating_ips(self, body, **kw):
        return (202, self.get_os_floating_ips_1()[1])

    def post_os_floating_ips(self, body):
        if body.get('pool'):
            return (200, {'floating_ip':
                    {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1',
                     'pool': 'cinder'}})
        else:
            return (200, {'floating_ip':
                    {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1',
                     'pool': None}})

    def delete_os_floating_ips_1(self, **kw):
        return (204, None)

    def get_os_floating_ip_dns(self, **kw):
        return (205, {'domain_entries':
                      [{'domain': 'example.org'},
                       {'domain': 'example.com'}]})

    def get_os_floating_ip_dns_testdomain_entries(self, **kw):
        if kw.get('ip'):
            return (205, {'dns_entries':
                          [{'dns_entry':
                            {'ip': kw.get('ip'),
                             'name': "host1",
                             'type': "A",
                             'domain': 'testdomain'}},
                           {'dns_entry':
                            {'ip': kw.get('ip'),
                             'name': "host2",
                             'type': "A",
                             'domain': 'testdomain'}}]})
        else:
            return (404, None)

    def get_os_floating_ip_dns_testdomain_entries_testname(self, **kw):
        return (205, {'dns_entry':
                      {'ip': "10.10.10.10",
                       'name': 'testname',
                       'type': "A",
                       'domain': 'testdomain'}})

    def put_os_floating_ip_dns_testdomain(self, body, **kw):
        if body['domain_entry']['scope'] == 'private':
            fakes.assert_has_keys(body['domain_entry'],
                                  required=['availability_zone', 'scope'])
        elif body['domain_entry']['scope'] == 'public':
            fakes.assert_has_keys(body['domain_entry'],
                                  required=['project', 'scope'])

        else:
            fakes.assert_has_keys(body['domain_entry'],
                                  required=['project', 'scope'])
        return (205, None)

    def put_os_floating_ip_dns_testdomain_entries_testname(self, body, **kw):
        fakes.assert_has_keys(body['dns_entry'],
                              required=['ip', 'dns_type'])
        return (205, None)

    def delete_os_floating_ip_dns_testdomain(self, **kw):
        return (200, None)

    def delete_os_floating_ip_dns_testdomain_entries_testname(self, **kw):
        return (200, None)

    #
    # Images
    #
    def get_images(self, **kw):
        return (200, {'images': [
            {'id': 1, 'name': 'CentOS 5.2'},
            {'id': 2, 'name': 'My Server Backup'}
        ]})

    def get_images_detail(self, **kw):
        return (200, {'images': [
            {
                'id': 1,
                'name': 'CentOS 5.2',
                "updated": "2010-10-10T12:00:00Z",
                "created": "2010-08-10T12:00:00Z",
                "status": "ACTIVE",
                "metadata": {
                    "test_key": "test_value",
                },
                "links": {},
            },
            {
                "id": 743,
                "name": "My Server Backup",
                "serverId": 1234,
                "updated": "2010-10-10T12:00:00Z",
                "created": "2010-08-10T12:00:00Z",
                "status": "SAVING",
                "progress": 80,
                "links": {},
            }
        ]})

    def get_images_1(self, **kw):
        return (200, {'image': self.get_images_detail()[1]['images'][0]})

    def get_images_2(self, **kw):
        return (200, {'image': self.get_images_detail()[1]['images'][1]})

    def post_images(self, body, **kw):
        assert body.keys() == ['image']
        fakes.assert_has_keys(body['image'], required=['serverId', 'name'])
        return (202, self.get_images_1()[1])

    def post_images_1_metadata(self, body, **kw):
        assert body.keys() == ['metadata']
        fakes.assert_has_keys(body['metadata'],
                              required=['test_key'])
        return (200,
                {'metadata': self.get_images_1()[1]['image']['metadata']})

    def delete_images_1(self, **kw):
        return (204, None)

    def delete_images_1_metadata_test_key(self, **kw):
        return (204, None)

    #
    # Keypairs
    #
    def get_os_keypairs(self, *kw):
        return (200, {"keypairs": [
            {'fingerprint': 'FAKE_KEYPAIR', 'name': 'test'}
        ]})

    def delete_os_keypairs_test(self, **kw):
        return (202, None)

    def post_os_keypairs(self, body, **kw):
        assert body.keys() == ['keypair']
        fakes.assert_has_keys(body['keypair'],
                              required=['name'])
        r = {'keypair': self.get_os_keypairs()[1]['keypairs'][0]}
        return (202, r)

    #
    # Virtual Interfaces
    #
    def get_servers_1234_os_virtual_interfaces(self, **kw):
        return (200, {"virtual_interfaces": [
            {'id': 'fakeid', 'mac_address': 'fakemac'}
        ]})

    #
    # Quotas
    #

    def get_os_quota_sets_test(self, **kw):
        return (200, {'quota_set': {
                      'tenant_id': 'test',
                      'metadata_items': [],
                      'volumes': 1,
                      'gigabytes': 1}})

    def get_os_quota_sets_test_defaults(self):
        return (200, {'quota_set': {
                      'tenant_id': 'test',
                      'metadata_items': [],
                      'volumes': 1,
                      'gigabytes': 1}})

    def put_os_quota_sets_test(self, body, **kw):
        assert body.keys() == ['quota_set']
        fakes.assert_has_keys(body['quota_set'],
                              required=['tenant_id'])
        return (200, {'quota_set': {
                      'tenant_id': 'test',
                      'metadata_items': [],
                      'volumes': 2,
                      'gigabytes': 1}})

    #
    # Quota Classes
    #

    def get_os_quota_class_sets_test(self, **kw):
        return (200, {'quota_class_set': {
                      'class_name': 'test',
                      'metadata_items': [],
                      'volumes': 1,
                      'gigabytes': 1}})

    def put_os_quota_class_sets_test(self, body, **kw):
        assert body.keys() == ['quota_class_set']
        fakes.assert_has_keys(body['quota_class_set'],
                              required=['class_name'])
        return (200, {'quota_class_set': {
                      'class_name': 'test',
                      'metadata_items': [],
                      'volumes': 2,
                      'gigabytes': 1}})

    #
    # VolumeTypes
    #
    def get_types(self, **kw):
        return (200, {
            'volume_types': [{'id': 1,
                              'name': 'test-type-1',
                              'extra_specs':{}},
                             {'id': 2,
                              'name': 'test-type-2',
                              'extra_specs':{}}]})

    def get_types_1(self, **kw):
        return (200, {'volume_type': {'id': 1,
                                      'name': 'test-type-1',
                                      'extra_specs': {}}})

    def post_types(self, body, **kw):
        return (202, {'volume_type': {'id': 3,
                                      'name': 'test-type-3',
                                      'extra_specs': {}}})

    def post_types_1_extra_specs(self, body, **kw):
        assert body.keys() == ['extra_specs']
        return (200, {'extra_specs': {'k': 'v'}})

    def delete_types_1_extra_specs_k(self, **kw):
        return(204, None)

    def delete_types_1(self, **kw):
        return (202, None)

    #
    # Hosts
    #
    def get_os_hosts_host(self, *kw):
        return (200, {'host':
                [{'resource': {'project': '(total)', 'host': 'dummy',
                  'cpu': 16, 'memory_mb': 32234, 'disk_gb': 128}},
                 {'resource': {'project': '(used_now)', 'host': 'dummy',
                  'cpu': 1, 'memory_mb': 2075, 'disk_gb': 45}},
                 {'resource': {'project': '(used_max)', 'host': 'dummy',
                  'cpu': 1, 'memory_mb': 2048, 'disk_gb': 30}},
                 {'resource': {'project': 'admin', 'host': 'dummy',
                  'cpu': 1, 'memory_mb': 2048, 'disk_gb': 30}}]})

    def get_os_hosts_sample_host(self, *kw):
        return (200, {'host': [{'resource': {'host': 'sample_host'}}], })

    def put_os_hosts_sample_host_1(self, body, **kw):
        return (200, {'host': 'sample-host_1',
                      'status': 'enabled'})

    def put_os_hosts_sample_host_2(self, body, **kw):
        return (200, {'host': 'sample-host_2',
                      'maintenance_mode': 'on_maintenance'})

    def put_os_hosts_sample_host_3(self, body, **kw):
        return (200, {'host': 'sample-host_3',
                      'status': 'enabled',
                      'maintenance_mode': 'on_maintenance'})

    def get_os_hosts_sample_host_startup(self, **kw):
        return (200, {'host': 'sample_host',
                      'power_action': 'startup'})

    def get_os_hosts_sample_host_reboot(self, **kw):
        return (200, {'host': 'sample_host',
                      'power_action': 'reboot'})

    def get_os_hosts_sample_host_shutdown(self, **kw):
        return (200, {'host': 'sample_host',
                      'power_action': 'shutdown'})

    def put_os_hosts_sample_host(self, body, **kw):
        result = {'host': 'dummy'}
        result.update(body)
        return (200, result)

    def post_shares_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(body.keys()) == 1
        action = body.keys()[0]
        if action == 'os-access_allow':
            assert body[action].keys() == ['access_type', 'access_to']
        elif action == 'os-access_deny':
            assert body[action].keys() == ['access_id']
        elif action == 'os-access_list':
            assert body[action] == None
        else:
            raise AssertionError("Unexpected share action: %s" % action)
        return (resp, _body)
