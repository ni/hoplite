"""
Module for providing a customized json serializer for Hoplite to use.

Hoplite requires a json serializer that:
    -Can handle mongo related objects(objectID, datetime)
    -Has a decoder that can return dictionaries ASCII(UTF-8 to be specific)
        keywords and text
    -Does not add information to your dictionary when decoding that it thinks
        may be useful like bson.json_util does for datetime objects.

    bson.json_util does most of this, so that's what we use for the most part.
        We copy and modify the
    bson.json_util.loads function and object hook in this module to make it
        satisfy the requirements described above.
"""

import base64
import datetime
import json
import re
import uuid

import bson
from bson import EPOCH_AWARE, EPOCH_NAIVE
from bson.binary import Binary
from bson.code import Code
from bson.dbref import DBRef
from bson.int64 import Int64
from bson.max_key import MaxKey
from bson.min_key import MinKey
from bson.objectid import ObjectId
from bson.regex import Regex
from bson.timestamp import Timestamp


from bson.json_util import dumps

_RE_OPT_TABLE = {
    "i": re.I,
    "l": re.L,
    "m": re.M,
    "s": re.S,
    "u": re.U,
    "x": re.X,
}


def hoplite_dumps(obj, *args, **kwargs):
    """
    Serializes a dictionary into unicode(unless specified otherwise)
    bson.json_util.dumps does exactly what hoplite needs, so that's what
    we call
    :param obj: Python dictionary to be serialized
    :param args: Please refer to online documentation for bson.json_util.dumps
        and json.dumps
    :param kwargs: Please refer to online documentation for
        bson.json_util.dumps and json.dumps
    :return: serialized obj in unicode
    """
    return dumps(obj, *args, **kwargs)


def hoplite_loads(s, *args, **kwargs):
    """
    Decodes a serialized dictionary.
    :param s: serialized dictionary
    :return: unserialized dictionary
    """
    compile_re = kwargs.pop('compile_re', True)
    ensure_tzinfo = kwargs.pop('ensure_tzinfo', False)
    encoding = kwargs.pop('encoding', 'utf-8')
    kwargs['object_hook'] = lambda dct: object_hook(dct, compile_re, ensure_tzinfo, encoding)
    return json.loads(s, *args, **kwargs)


def object_hook(dct, compile_re=False, ensure_tzinfo=True, encoding=None):
    """
    Object hook used by hoplite_loads. This object hook can encode the
    dictionary in the right text format.  For example, json.loads by default
    will decode '{'hey':'hey'}' into {u'hey':u'hey'} rather than {'hey':'hey'}.
    If encoding is set to utf-8, this object_hook can make '{'hey':'hey'}'
    decode to {'hey':'hey'} This object hook also decodes extended json types
    such as objectId and datetime objects. Datetime objects also
    have the option to be decoded with or without timezone information.
    :param dct: Dictionary this object hook is to operate on.
    :param ensure_tzinfo: Boolean deciding if timezone info should be added to
        decoded datetime objects
    :param encoding: choice of text decoding(unicode/utf-8, perhaps others)
    :return:
    """

    if encoding:
        # Converts all keys and unicode values in the top layer of the current
        # dictionary to the desired encoding type.
        new_dct = {}
        for key, value in dct.iteritems():
            if isinstance(key, unicode):
                key = key.encode(encoding)
            if isinstance(value, unicode):
                value = value.encode(encoding)
            new_dct[key] = value
        dct = new_dct

    if "$oid" in dct:
        return ObjectId(str(dct["$oid"]))
    if "$ref" in dct:
        return DBRef(dct["$ref"], dct["$id"], dct.get("$db", None))
    if "$date" in dct:
        secs = float(dct["$date"]) / 1000.0
        if ensure_tzinfo:
            return EPOCH_AWARE + datetime.timedelta(seconds=secs)
        else:
            # Avoid adding time zone info by default, unlike
            # bson.json_util.loads. If the developer really wants this, they
            # will have to specify it.
            return EPOCH_NAIVE + datetime.timedelta(seconds=secs)

    if "$regex" in dct:
        flags = 0
        # PyMongo always adds $options but some other tools may not.
        for opt in dct.get("$options", ""):
            flags |= _RE_OPT_TABLE.get(opt, 0)
        if compile_re:
            return re.compile(dct["$regex"], flags)
        else:
            return Regex(dct["$regex"], flags)
    if "$minKey" in dct:
        return MinKey()
    if "$maxKey" in dct:
        return MaxKey()
    if "$binary" in dct:
        if isinstance(dct["$type"], int):
            dct["$type"] = "%02x" % dct["$type"]
        subtype = int(dct["$type"], 16)
        if subtype >= 0xffffff80:  # Handle mongoexport values
            subtype = int(dct["$type"][6:], 16)
        return Binary(base64.b64decode(dct["$binary"].encode()), subtype)
    if "$code" in dct:
        return Code(dct["$code"], dct.get("$scope"))
    if "$uuid" in dct:
        return uuid.UUID(dct["$uuid"])
    if "$undefined" in dct:
        return None
    if "$numberLong" in dct:
        return Int64(dct["$numberLong"])
    if "$timestamp" in dct:
        tsp = dct["$timestamp"]
        return Timestamp(tsp["t"], tsp["i"])
    return dct


if __name__ == '__main__':
    dictionary = {
                        "uuid": "correctuuid",
                        "name": "test_plugins.wait_10_seconds",
                        "config": {"something": "is missing"},
                        "status":
                        {
                            "Roger": "Roger what's your status?",
                            "anumber": 123,
                            "objectid": bson.objectid.ObjectId(),
                            "datetime": datetime.datetime.now(),
                            "regexp": re.compile("hoplite")
                        },
                        "running": True,
                        "finished": False

                }
    print hoplite_dumps(dictionary)
    dictionary_bson_back = hoplite_loads(
        hoplite_dumps(hoplite_loads(hoplite_dumps(dictionary))))
    print dictionary
    print dictionary_bson_back
    print "Dictionaries are the same: " + str((
        dictionary == dictionary_bson_back))
