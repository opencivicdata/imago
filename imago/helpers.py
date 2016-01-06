# Copyright (c) Sunlight Foundation, 2014, under the BSD-3 License.
# Authors:
#    - Paul R. Tagliamonte <paultag@sunlightfoundation.com>


from django.core.paginator import Paginator, EmptyPage
from django.core.exceptions import FieldError, ObjectDoesNotExist
from restless.modelviews import ListEndpoint, DetailEndpoint
from restless.models import serialize
from restless.http import HttpError, Http200
from collections import defaultdict
from django.conf import settings
from django.db import connections

import datetime
import math


def get_field_list(model, without=None):
    """
    Get a list of all known field names on a Django model. Optionally,
    you may exclude keys by passing a list of keys to avoid in the 'without'
    kwarg.
    """
    if without is None:
        without = set()
    else:
        without = set(without)
    return list({f.name for f in model._meta.get_fields()} - without)


class FieldKeyError(KeyError):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        return "<FieldKeyError: %s>" % (self.field)


def get_fields(root, fields):
    """
    Return a list of objects to prefetch and a composed spec for the
    DjangoRestless serialize call given a root spec dictionary and a list
    of fields.

    Fields may be dotted to represent sub-elements, which will
    traverse the root dictonary.

    This function returns a tuple, prefetch-able fields, and a serialize
    function spec. The result of the latter may be passed directly into
    serialize, and will limit based on `fields`, rather then `include` or
    `exclude`.
    """

    def fwrap(obj, memo=None):
        """
        Ensure this object can be passed into serialize by turning it from
        a raw structure dict into a serialize spec. Most of the time
        this is just wrapping dicts in {"fields": ...}.
        """
        memo = memo if memo else set()
        id_ = id(obj)
        if id_ in memo:
            return None
        memo.add(id_)

        if isinstance(obj, dict):
            if obj == {} or obj.get("fields"):
                return obj
            obj = list(filter(
                lambda x: x[1] != None,
                [(x, fwrap(y, memo=memo)) for x, y in obj.items()]
            ))
            if obj == []:
                return None
            return {"fields": obj}
        return obj

    prefetch = set([])
    subfields = defaultdict(list)
    concrete = []
    for field in fields:
        if '.' not in field:
            concrete.append(field)
            continue
        prefix, postfix = field.split(".", 1)

        if '.' not in postfix:
            prefetch.add(prefix)

        subfields[prefix].append(postfix)

    try:
        ret = {x: fwrap(root[x]) for x in concrete}
    except KeyError as e:
        raise FieldKeyError(*e.args)

    for key, fields in subfields.items():
        try:
            _prefetch, ret[key] = get_fields(root[key], fields)
        except FieldKeyError as e:
            e.field = "%s.%s" % (key, e.field)
            raise e

        prefetch = prefetch.union({"%s__%s" % (key, x) for x in _prefetch})
    return (prefetch, fwrap(ret))


def cachebusterable(fn):
    """
    Allow front-end tools to pass a "_" pararm with different arguments
    to work past cache. This is the default behavior for select2, and was
    easy enough to avoid.

    This ensures we don't get "_" in the view handler, avoding special
    casing in multiple places.
    """
    def _(self, request, *args, **kwargs):
        params = request.params
        if '_' in params:
            params.pop("_")
        return fn(self, request, *args, **kwargs)
    return _


def no_authentication_or_is_authenticated(request):
    return (not hasattr(settings, 'USE_LOCKSMITH') or not settings.USE_LOCKSMITH
            or hasattr(request, 'apikey') and request.apikey.status == 'A')

def authenticated(fn):
    """ ensure that request.apikey is valid """
    def _(self, request, *args, **kwargs):
        if no_authentication_or_is_authenticated(request):
            if 'apikey' in request.params:
                request.params.pop('apikey')

            return fn(self, request, *args, **kwargs)
        else:
            raise HttpError(403, "Authorization Required: obtain a key at " +
                            settings.LOCKSMITH_REGISTRATION_URL)
    return _


class DebugMixin(object):

    def start_debug(self):
        if settings.DEBUG:
            self.start_time = datetime.datetime.utcnow()
            self.start_queries = len(connections['default'].queries)

    def get_debug(self):
        if settings.DEBUG:
            end_time = datetime.datetime.utcnow()
            connection = connections['default']
            end_queries = len(connection.queries)

            return {
                "connection": {
                    "query": {
                        "count_start": self.start_queries,
                        "count_end": end_queries,
                        "count": (end_queries - self.start_queries),
                        "list": connection.queries,
                    },
                    "dsn": connection.connection.dsn,
                    "vendor": connection.vendor,
                    "pg_version": connection.pg_version,
                    "psycopg2_version": ".".join([
                        str(x) for x in connection.psycopg2_version
                    ])
                },
                "time": {
                    "start": self.start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "seconds": (end_time - self.start_time).total_seconds()
                },
            }


class PublicListEndpoint(ListEndpoint, DebugMixin):
    """
    Imago public list API helper class.

    This class exists to be subclassed by concrete views, and builds in
    sane default behavior for all list views.

    Critically it allows for:

         - Filtering
         - Sorting
         - Pagination
         - Meta-dictionary for the clients
         - Opinionated serializion with the helpers above.

    This allows our views to be declarative, and allow for subclass overriding
    of methods when needed.

    Access-Control-Allow-Origin is currently always set to "*", since this
    is a global read-only API.

    As a result, JSONP is disabled. Read more on using CORS:
       - http://en.wikipedia.org/wiki/Cross-origin_resource_sharing

    The 'get' class-based view method invokes the following helpers:


        [ Methods ]
         - get_query_set  | Get the Django query set for the request.
         - filter         | Filter the resulting query set.
         - sort           | Sort the filtered query set
         - paginate       | Paginate the sorted query set


        [ Object Properties ]
         - model            | Django ORM Model / class to query using.
         - per_page         | Objects to show per-page.

         - default_fields   | If no `fields` param is passed in, use this
                            | to limit the `serialize_config`.

         - serialize_config | Object serializion to use. Many are in
                            | the imago.serialize module
    """

    methods = ['GET']
    max_per_page = 100
    serialize_config = {}
    default_fields = []

    def adjust_filters(self, params):
        """
        Adjust the filter params from within the `filter' call.
        """
        return params

    def filter(self, data, **kwargs):
        """
        Filter the Django query set.

        THe kwargs will be unpacked into Django directly, letting you
        use full Django query syntax here.
        """
        kwargs = self.adjust_filters(kwargs)
        try:
            return data.filter(**kwargs)
        except FieldError:
            raise HttpError(400, "Error: You've passed an invalid filter parameter.")
        except Exception:
            raise HttpError(500, "Error: Something went wrong with your request")

    def sort(self, data, sort_by):
        """
        Sort the Django query set. The sort_by param will be
        unpacked into 'order_by' directly.
        """
        return data.order_by(*sort_by)

    def paginate(self, data, page, per_page):
        """
        Paginate the Django response. It will default to
        `self.per_page` as the `per_page` argument to the built-in
        Django `Paginator`. This will return `paginator.page` for the
        page number passed in.
        """
        paginator = Paginator(data, per_page=per_page)
        return paginator.page(page)

    @authenticated
    @cachebusterable
    def get(self, request, *args, **kwargs):
        """
        Default 'GET' class-based view.
        """

        params = request.params

        # default to page 1
        page = int(params.pop('page', 1))
        per_page = min(self.max_per_page, int(params.pop('per_page', self.max_per_page)))

        sort_by = []
        if 'sort' in params:
            sort_by = params.pop('sort').split(",")

        fields = self.default_fields
        if 'fields' in params:
            fields = params.pop('fields').split(",")

        data = self.get_query_set(request, *args, **kwargs)
        data = self.filter(data, **params)
        data = self.sort(data, sort_by)

        try:
            related, config = get_fields(self.serialize_config, fields=fields)
        except FieldKeyError as e:
            raise HttpError(400, "Error: You've asked for a field ({}) that "
                            "is invalid. Valid fields are: {}".format(
                                e.field, ', '.join(self.serialize_config.keys()))
                           )
        except KeyError as e:
            raise HttpError(400, "Error: Invalid field: %s" % (e))

        data = data.prefetch_related(*related)

        try:
            data_page = self.paginate(data, page, per_page)
        except EmptyPage:
            raise HttpError(404, 'No such page (heh, literally - its out of bounds)')

        self.start_debug()

        count = data_page.paginator.count

        response = {
            "meta": {
                "count": len(data_page.object_list),
                "page": page,
                "per_page": per_page,
                "max_page": math.ceil(count / per_page),
                "total_count": count,
            }, "results": [
                serialize(x, **config) for x in data_page.object_list
            ]
        }

        if settings.DEBUG:
            response['debug'] = self.get_debug()
            response['debug'].update({
                "prefetch_fields": list(related),
                "page": page,
                "sort": sort_by,
                "field": fields,
            })

        response = Http200(response)

        response['Access-Control-Allow-Origin'] = "*"
        return response


class PublicDetailEndpoint(DetailEndpoint, DebugMixin):
    """
    Imago public detail view API helper class.

    This class exists to be subclassed by concrete views, and builds in
    sane default behavior for all list views.

    This allows our views to be declarative, and allow for subclass overriding
    of methods when needed.

    Access-Control-Allow-Origin is currently always set to "*", since this
    is a global read-only API.

    As a result, JSONP is disabled. Read more on using CORS:
       - http://en.wikipedia.org/wiki/Cross-origin_resource_sharing


    The 'get' class-based view method uses the following object properties:

         - model            | Django ORM Model / class to query using.

         - default_fields   | If no `fields` param is passed in, use this
                            | to limit the `serialize_config`.

         - serialize_config | Object serializion to use. Many are in
                            | the imago.serialize module
    """

    methods = ['GET']

    @authenticated
    @cachebusterable
    def get(self, request, pk, *args, **kwargs):
        params = request.params

        fields = self.default_fields
        if 'fields' in params:
            fields = params.pop('fields').split(",")

        related, config = get_fields(self.serialize_config, fields=fields)

        self.start_debug()

        try:
            obj = self.model.objects.prefetch_related(*related).get(pk=pk)
        except ObjectDoesNotExist as e:
            raise HttpError(404, "Error: {}".format(e))
        except Exception:
            raise HttpError(500, "Error: Something went wrong with your request")

        serialized = serialize(obj, **config)
        serialized['debug'] = self.get_debug()

        response = Http200(serialized)
        response['Access-Control-Allow-Origin'] = "*"

        return response
