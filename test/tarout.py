from tarfile import TarFile, TarInfo
from cStringIO import StringIO
from pupa.core import db
from pupa.utils import JSONEncoderPlus
import json

from contextlib import contextmanager


@contextmanager
def buffer():
    s = StringIO()
    try:
        yield s
    except:
        s.close()
        raise


def iterate_members(jurisdictions):
    spec = {"jurisdiction_id": {"$in": jurisdictions}}

    for collection in [
        db.bills,
        db.votes,
        db.events,
        db.organizations,
    ]:
        for entry in collection.find(spec, timeout=False):
            yield ("{jurisdiction}/{id}".format(
                jurisdiction=entry['jurisdiction_id'],
                id=entry['_id']
            ), entry)





def generate_tarball(data):
    with buffer() as output:
        tf = TarFile(fileobj=output, mode='w')
        for path, datum in data:
            with buffer() as string:
                json.dump(datum, string, cls=JSONEncoderPlus)
                info = TarInfo(name=path)
                info.size = string.tell()
                string.seek(0)
                tf.addfile(tarinfo=info, fileobj=string)
        output.seek(0)
        return output.getvalue()


def generate_tarball_dump(jurisdictions):
    return generate_tarball(iterate_members(jurisdictions))


print generate_tarball_dump([
    'ocd-jurisdiction/country:us/state:mt/legislature'
])
