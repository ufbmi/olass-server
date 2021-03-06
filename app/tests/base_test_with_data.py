"""
Goal: Extend the base test class by inserting sample rows in the database

Authors:
     Andrei Sura <sura.andrei@gmail.com>
"""
# import uuid
from mock import patch
from hashlib import sha256
from binascii import unhexlify
from binascii import hexlify
from sqlalchemy.orm.exc import MultipleResultsFound

from base_test import BaseTestCase
from olass import utils
from olass.main import db

from olass.models.person import Person
from olass.models.partner_entity import PartnerEntity
from olass.models.linkage_entity import LinkageEntity
from olass.models.oauth_user_entity import OauthUserEntity
from olass.models.oauth_user_role_entity import OauthUserRoleEntity
from olass.models.oauth_role_entity import OauthRoleEntity
from olass.models.oauth_client_entity import OauthClientEntity
from olass.models.oauth_access_token_entity import OauthAccessTokenEntity


VERBOSE = False
COUNT = 0

# _1 First Name + Last Name + DOB + Zip
RULE_CODE_F_L_D_Z = 'F_L_D_Z'

# _2 Last Name + First Name + DOB + Zip
RULE_CODE_L_F_D_Z = 'L_F_D_Z'

# _3 First Name + Last Name + DOB + City
RULE_CODE_F_L_D_C = 'F_L_D_C'

# _4 Last Name + First Name + DOB + City
RULE_CODE_L_F_D_C = 'L_F_D_C'

# _5 Three Letter FN + Three Letter LN + Soundex FN + Soundex LN + DOB
RULE_CODE_3F_3L_SF_SL_D = '3F_3L_SF_SL_D'

RULE_MAP = {
    RULE_CODE_F_L_D_Z: '{0.first}{0.last}{0.dob}{0.zip}',
    RULE_CODE_L_F_D_Z: '{0.last}{0.first}{0.dob}{0.zip}',
}


def verbose(msg):
    if VERBOSE:
        print("==> {}".format(msg))


def apply_sha256(val):
    """ Compute sha256 sum
    :param val: the input string
    :rtype string: the sha256 hexdigest
    """
    m = sha256()
    m.update(val.encode('utf-8'))
    return m.hexdigest()


def get_person_hash(person, rules):
    """
    Get a dictionary of unhexlified hashes for a person object
    """
    hashes = {}

    for rule in rules:
        pattern = RULE_MAP.get(rule)
        raw = pattern.format(person)
        unhex = unhexlify(apply_sha256(raw))
        hashes[rule] = unhex
        # print("Apply unhexlify(sha256({})) = {}".format(raw, unhex))

    return hashes


class BaseTestCaseWithData(BaseTestCase):

    """ Add data... """

    def setUp(self):
        db.create_all()
        self.create_partners()
        self.create_sample_data()
        self.create_oauth_users()

    def create_partners(self):
        """
        Create rows
        """
        added_date = utils.get_db_friendly_date_time()
        partner_uf = PartnerEntity.create(
            partner_code="UF",
            partner_description="University of Florida",
            partner_added_at=added_date)

        partner_fh = PartnerEntity.create(
            partner_code="FH",
            partner_description="Florida Hospital",
            partner_added_at=added_date)

        self.assertIsNotNone(partner_uf.id)
        self.assertIsNotNone(partner_fh.id)
        self.assertEquals("UF", partner_uf.partner_code)
        self.assertEquals("FH", partner_fh.partner_code)

        # verify that more than one
        with self.assertRaises(MultipleResultsFound):
                PartnerEntity.query.filter(
                    PartnerEntity.
                    partner_description.like(
                        '%Florida%')).one()

    def dummy_get_uuid_bin(*args, **kwargs):
        """
        Patch the get_uuid_bin() so we can get predictable UUIDs
        usable in test_integration.py
        """
        global COUNT
        COUNT = COUNT + 1 if COUNT < 8 else 0
        uuid_text = "{}09949141ba811e69454f45c898e9b67".format(COUNT)
        return unhexlify(str(uuid_text).replace('-', '').lower().encode())

    @patch.multiple(utils, get_uuid_bin=dummy_get_uuid_bin)
    def create_sample_data(self):
        """ Add some data """
        added_date = utils.get_db_friendly_date_time()

        sample_data = [
            {"first": "Aida", "last": " Xenon", "dob": "1910-11-12",
                "zip": "19116", "city": "GAINESVILLE"},
            {"first": "aida", "last": "xeNon ", "dob": "1910/11/12",
                "zip": "19116", "city": "gainesville"},
            {"first": "AIDA", "last": "XENON ", "dob": "1910:11:12  ",
                "zip": "19116", "city": "Gainesville"},
            {"first": "AiDa", "last": "XEnON ", "dob": "19101112  ",
                "zip": "19116", "city": "gainesviLLe"},
            {"first": "John", "last": "Doe", "dob": "1900-01-01",
                "zip": "32606", "city": "Palatca"},
            {"first": "JOHN", "last": "DOE", "dob": "1900-01-01",
                "zip": "32607", "city": "Palatca"}, ]

        partner = PartnerEntity.query.filter_by(
            partner_code='UF').one()

        # Note: first four entries produce the same hashes (aka chunks)
        for person_data in sample_data:
            person_orig = Person(person_data)
            person = Person.get_prepared_person(person_data)
            pers_uuid = utils.get_uuid_bin()
            hashes = get_person_hash(person,
                                     [RULE_CODE_F_L_D_Z, RULE_CODE_L_F_D_Z])

            for rule_id, ahash in hashes.items():
                link = LinkageEntity.create(
                    partner_id=partner.id,
                    linkage_uuid=pers_uuid,
                    linkage_hash=ahash,
                    linkage_added_at=added_date)
                self.assertIsNotNone(link)

                links_by_hash = LinkageEntity.query.filter_by(
                    linkage_hash=ahash).all()

                verbose("==> Found {} link(s) for [{}] using hash: {}"
                        .format(
                            len(links_by_hash),
                            person_orig,
                            hexlify(ahash)))

    def create_oauth_users(self):
        """ Add user, role, user_role
        Note: partners should exist
        """
        added_at = utils.get_db_friendly_date_time()
        expires_date = utils.get_expiration_date(10)
        expires_date2 = utils.get_expiration_date(0)

        ##############
        # add role row
        role = OauthRoleEntity.create(
            role_code='root',
            role_description='super-user can do xyz...'
        )
        self.assertEquals(1, role.id)
        role = OauthRoleEntity.get_by_id(1)
        self.assertIsNotNone(role)
        verbose(role)

        ##############
        # add user row
        user = OauthUserEntity.create(
            email='asura-root@ufl.edu',
            password_hash='$6$rounds=666140$vQVDNQUwZCSDY0u7$kqmaQjQnYwWz9EQlms99UQDYaphVBwujnUs1H3XdhT741pY1HPirG1Y.oydcw3QtQnaMyVOspVZ20Dij7f24A/',  # NOQA
            added_at=added_at
        )
        self.assertEquals(1, user.id)
        verbose(user)

        ##############
        # add user_role row
        partner = PartnerEntity.query.filter_by(partner_code="UF").one()
        verbose(partner)

        user_role = OauthUserRoleEntity.create(
            partner_id=partner.id,
            user_id=user.id,
            role_id=role.id,
            added_at=added_at
        )
        user_role = OauthUserRoleEntity.get_by_id(1)
        self.assertIsNotNone(user_role)
        verbose(user_role)

        ##############
        # Verify that the user now is properly mapped to a partner and a role
        user = OauthUserEntity.get_by_id(1)
        self.assertIsNotNone(user.partner)
        self.assertIsNotNone(user.role)
        verbose(user)

        ##############
        # Verify that we can save a client, grant code, access token
        client = OauthClientEntity.create(
            client_id='client_1',
            client_secret='secret_1',
            user_id=user.id,
            added_at=added_at)

        client2 = OauthClientEntity.create(
            client_id='client_2',
            client_secret='secret_2',
            user_id=user.id,
            added_at=added_at)

        token = OauthAccessTokenEntity.create(
            client_id=client.client_id,
            token_type='Bearer',
            access_token='access_token_1',
            refresh_token='refresh_token_1',
            expires=expires_date,
            added_at=added_at)

        token2 = OauthAccessTokenEntity.create(
            client_id=client2.client_id,
            token_type='Bearer',
            access_token='access_token_2',
            refresh_token='',
            expires=expires_date2,
            added_at=added_at)

        self.assertIsNotNone(client.id)
        self.assertIsNotNone(client2.id)
        self.assertIsNotNone(token.id)
        self.assertIsNotNone(token2.id)

        # Verify the token properties
        self.assertIsNotNone(token.client)
        self.assertIsNotNone(token.client.user)
        self.assertIsNotNone(token.user)
        self.assertIsNotNone(token.user.id)
        ser = token.serialize()
        self.assertIsNotNone(ser.get('id'))
        self.assertIsNotNone(ser.get('access_token'))
        self.assertIsNotNone(ser.get('expires_in'))

        client = OauthClientEntity.get_by_id(1)
        client2 = OauthClientEntity.query.filter_by(client_id='client_1').one()
        role = OauthUserRoleEntity.get_by_id(1)

        self.assertIsNotNone(client)
        self.assertIsNotNone(client2)
        self.assertIsNotNone(role)
        verbose("Expect client: {}".format(client))
        verbose("Expect token: {}".format(token))
        verbose("Expect token serialized: {}".format(token.serialize()))
        verbose("Expect token2 serialized: {}".format(token2.serialize()))
