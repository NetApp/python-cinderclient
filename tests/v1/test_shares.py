from cinderclient.v1 import shares
from tests import utils
from tests.v1 import fakes


cs = fakes.FakeClient()


class SharesTest(utils.TestCase):

    def test_create_nfs_share(self):
        cs.shares.create('nfs', 1)
        cs.assert_called('POST', '/shares')

    def test_create_cifs_share(self):
        cs.shares.create('cifs', 2)
        cs.assert_called('POST', 'shares')

    def test_delete_share(self):
        share = cs.shares.get('1234')
        cs.shares.delete(share)
        cs.assert_called('DELETE', '/shares/1234')

    def test_list_shares(self):
        cs.shares.list()
        cs.assert_called('POST', '/shares')

    def test_allow_access_to_share(self):
        share = cs.shares.get(1234)
        ip = '192.168.0.1'
        cs.shares.allow(share, 'ip', ip)
        cs.assert_called('POST', '/shares/1234/action')
