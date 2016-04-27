"""
Goal: Delegate requests to the `/api` path to the appropriate controller

@authors:
    Andrei Sura <sura.andrei@gmail.com>
"""
import collections
from binascii import unhexlify
from flask import request
# from flask import session
# from flask import make_response
# from flask_login import login_required

from olass import utils
from olass.main import app
from olass.models.partner_entity import PartnerEntity
from olass.models.rule_entity import RuleEntity
from olass.models.linkage_entity import LinkageEntity


@app.route('/api/', methods=['POST', 'GET'])
# @login_required
def api_hello():
    """ Say hello """
    return utils.jsonify_success({
        'message': 'Hello'
    })


@app.route('/api/check', methods=['POST', 'GET'])
def api_check_existing():
    """
    For each chunk verify if it exists in the database.

== Example input json:

{
  "partner_code": "UF",
  "data": {
"1":
[{"rule_code": "F_L_D_Z",
  "chunk": "8a31efa965d46f971426ac9c133db1c769a712657b74410016d636b10a996506"},
 {"rule_code": "F_L_D_Z",
   "chunk": "db07840bf253e5e6c16cabaca97fcc4363643f8552d65ec04290f3736d72b27d"},
 {"rule_code": "F_L_D_Z",
   "chunk": "c79db51a3f0037ef83f45b4a85bc519665dbf9de8adf9f47d4a73a0c5bb91caa"}]
}
}

== Example of output json:
{
"status": "success",
"data": {
    "1": {
        "8a31efa965d46f971426ac9c133db1c769a712657b74410016d636b10a996506": {
            "is_found": 1,
            "rule": "F_L_D_Z"
        },
        "c79db51a3f0037ef83f45b4a85bc519665dbf9de8adf9f47d4a73a0c5bb91caa": {
            "is_found": 1,
            "rule": "F_L_D_Z"
        },
        "db07840bf253e5e6c16cabaca97fcc4363643f8552d65ec04290f3736d72b27d": {
            "is_found": 1,
            "rule": "L_F_D_Z"
        }
    }
}
}
    """
    json = request.get_json(silent=False)
    if not json:
        err = "Invalid json object specified"
        app.logger.error(err)
        return utils.jsonify_error(err)

    app.logger.info("call api_check_existing() from partner: {}"
                    .format(json['partner_code']))

    result = collections.defaultdict(dict)

    # init the response dictionary
    for pat_id, pat_chunks in json['data'].items():
        chunks = [x.get('chunk') for x in pat_chunks]
        result[pat_id] = dict.fromkeys(chunks)

    # patient chunks are received in groups
    for pat_id, pat_chunks in json['data'].items():
        chunks = [x.get('chunk') for x in pat_chunks]

        for chunk in chunks:
            if len(chunk) != 64:
                app.logger.warn("Skip chunk for patient [{}] with length: {}"
                                .format(pat_id, len(chunk)))
                continue

            app.logger.info("check pat_id [{}] chunk: {}".format(pat_id, chunk))
            binary_hash = unhexlify(chunk)
            link = LinkageEntity.query.filter_by(
                linkage_hash=binary_hash).one_or_none()

            if link:
                result[pat_id][chunk] = \
                    {"is_found": 1, "rule": link.rule.rule_code}
            else:
                result[pat_id][chunk] = {"is_found": 0}

    return utils.jsonify_success(result)


@app.route('/api/save', methods=['POST', 'GET'])
def api_save_patient_hashes():
    """
    For each chunk save a new uuid or return an existing one from the database.

== Example of input json:
{
  "partner_code": "UF",
  "data":
{
"1":
[{"rule_code": "F_L_D_Z",
  "chunk": "8a31efa965d46f971426ac9c133db1c769a712657b74410016d636b10a996506"},
 {"rule_code": "F_L_D_Z",
   "chunk": "db07840bf253e5e6c16cabaca97fcc4363643f8552d65ec04290f3736d72b27d"},
 {"rule_code": "F_L_D_Z",
   "chunk": "c79db51a3f0037ef83f45b4a85bc519665dbf9de8adf9f47d4a73a0c5bb91caa"}
 ]
}
}

== Example of output json:
{
"status": "success",
"data": {
    "1": {
        "8a31efa965d46f971426ac9c133db1c769a712657b74410016d636b10a996506": {
            "rule": "F_L_D_Z",
            "uuid": "4d4f951c0beb11e68fb0f45c898e9b67"
        },
        "c79db51a3f0037ef83f45b4a85bc519665dbf9de8adf9f47d4a73a0c5bb91caa": {
            "rule": "F_L_D_Z",
            "uuid": "4d4f951c0beb11e68fb0f45c898e9b67"
        },
        "db07840bf253e5e6c16cabaca97fcc4363643f8552d65ec04290f3736d72b27d": {
            "rule": "L_F_D_Z",
            "uuid": "4d4f951c0beb11e68fb0f45c898e9b67"
        }
    }
}
}
    """
    json = request.get_json(silent=False)

    if not json:
        err = "Invalid json object specified"
        app.logger.error(err)
        return utils.jsonify_error(err)

    app.logger.info("call api_save_patient_hashes() "
                    "from partner_code [{}] for [{}] patients"
                    .format(json['partner_code'], len(json['data'].keys())))

    result = collections.defaultdict(dict)

    # init the response dictionary
    for pat_id, pat_chunks in json['data'].items():
        chunks = [x.get('chunk') for x in pat_chunks]
        result[pat_id] = dict.fromkeys(chunks)

    # @TODO: move input validation to a dedicated function
    # find the proper partner id
    partner_code = json['partner_code']

    if not (1 <= len(partner_code) <= 5):
        raise Exception("Invalid partner code length: {}"
                        .format(len(partner_code)))
    partner = PartnerEntity.query.filter_by(
        partner_code=partner_code).one_or_none()
    rules_cache = RuleEntity.get_rules_cache()

    if not partner:
        raise Exception("Invalid partner code: {}".format(partner_code))

    # patient chunks are received in groups
    for pat_id, pat_chunks in json['data'].items():
        chunks = [x.get('chunk') for x in pat_chunks]
        chunks_cache = LinkageEntity.get_chunks_cache(chunks)
        uuids = LinkageEntity.get_distinct_uuids_for_chunks(chunks_cache)
        app.logger.info("Found [{}] matching uuids from [{}] chunks of patient "
                        "[{}]".format(len(uuids), len(chunks), pat_id))

        if len(uuids) == 0:
            app.logger.info("generate new uuid for pat_id [{}]".format(pat_id))
            binary_uuid = utils.get_uuid_hex()

            for chunk_data in pat_chunks:
                # link every chunk to the same uuid
                added_date = utils.get_db_friendly_date_time()
                chunk = chunk_data['chunk']
                rule_code = chunk_data['rule_code']
                binary_hash = unhexlify(chunk.encode('utf-8'))

                link = LinkageEntity.create(
                    partner_id=partner.id,
                    rule_id=rules_cache.get(rule_code),
                    linkage_uuid=binary_uuid,
                    linkage_hash=binary_hash,
                    linkage_addded_at=added_date)

                # update the response json
                result[pat_id][chunk] = \
                    {"uuid": link.friendly_uuid(), "rule": link.rule.rule_code}

        elif len(uuids) == 1:
            uuid = uuids.pop()
            app.logger.info("Reusing the uuid [{}]".format(uuid))

            for chunk_data in pat_chunks:
                # link every chunk to the same uuid
                chunk = chunk_data['chunk']
                rule_code = chunk_data['rule_code']
                binary_hash = unhexlify(chunk.encode('utf-8'))
                binary_uuid = unhexlify(uuid.encode('utf-8'))
                link = chunks_cache.get(chunk)

                if not link:
                    app.logger.info("Attempt to insert for hash [{}]"
                                    .format(chunk))
                    added_date = utils.get_db_friendly_date_time()
                    link = LinkageEntity.create(
                        partner_id=partner.id,
                        rule_id=rules_cache.get(rule_code),
                        linkage_uuid=binary_uuid,
                        linkage_hash=binary_hash,
                        linkage_addded_at=added_date)
                result[pat_id][chunk] = \
                    {"uuid": link.friendly_uuid(), "rule": link.rule.rule_code}

        else:
            app.logger.error("It looks like we got a collision for chunks: {}"
                             .format(chunks, uuids))
            raise Exception("More than one uuid for chunks attributed to"
                            "[{}] patient [{}]".format(partner_code, pat_id))

        for chunk_data in pat_chunks:
            chunk = chunk_data['chunk']
            rule_code = chunk_data['rule_code']

            # validate the input
            if len(chunk) != 64:
                app.logger.warn("Skip chunk for patient [{}] with length: {}"
                                .format(pat_id, len(chunk)))
                continue

            if not (1 <= len(rule_code) <= 255):
                raise Exception("Invalid rule_code length: {}"
                                .format(len(rule_code)))

            rule = RuleEntity.query.filter_by(rule_code=rule_code).one_or_none()
            if not rule:
                raise Exception("No such rul_codee: {}".format(rule_code))

    return utils.jsonify_success(result)
