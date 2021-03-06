"""
Goal: test search event

Authors:
    Andrei Sura <sura.andrei@gmail.com>

"""

from binascii import unhexlify

from base_test_with_data import BaseTestCaseWithData
from olass.models.partner_entity import PartnerEntity
from olass.models.linkage_entity import LinkageEntity


class TestFindPerson(BaseTestCaseWithData):

    def test_find_person(self):
        """
        Verify we can read from the database.
        Note: sample rows are inserted by the parent class
        """
        link = LinkageEntity.get_by_id(1)
        partner_uf = PartnerEntity.query.filter_by(partner_code='UF')
        binary_hash = unhexlify(
            'b2cdaea3d7c9891b2ed94d1973fe5085183e4bb4bd87b672e066a456ee67bd38')
        links = LinkageEntity.query.filter_by(linkage_hash=binary_hash).all()
        self.assertIsNotNone(link)
        self.assertIsNotNone(partner_uf)
        # print("\nLinks in the database: {}".format(len(links)))

        for link in links:
            self.assertIsNotNone(link)
            # print(link)
