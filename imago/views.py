import json
from django.http import HttpResponse
from django.views.generic.base import View
from imago.core import db


def _clamp(val, _min, _max):
    return _min if val < _min else _max if val > _max else val


class JsonView(View):
    """ Base view for writing API views

    Properties to set:
        collection - collection to query
        find_one - use find_one instead of find in lookup
            (optional - default False)
        default_fields - mongodb fields parameter if not specified
            (optional - defaults to all)

    query_from_request(self, request, *args)
    sort_from_request(self, request)
    """

    find_one = False
    default_fields = None
    per_page = 100
    max_per_page = 200

    def get(self, request, *args, **kwargs):
        data = self.get_data(request, *args, **kwargs)

        if self.find_one:
            pass
        else:
            total = data.count()
            per_page = _clamp(int(request.GET.get('per_page', self.per_page)),
                              1, self.max_per_page)
            page = _clamp(int(request.GET.get('page', 0)), 0, total/per_page)
            data = list(data.skip(page*per_page).limit(per_page))
            data = {'results': data, 'meta': {'page': page,
                                              'per_page': per_page,
                                              'count': len(data),
                                              'total_count': total,
                                              'pages': total/per_page,
                                             }
                   }

        data = json.dumps(self._clean(data),
                          # cls=DateTimeAwareJSONEncoder,
                          ensure_ascii=False)

        # JSONP
        cb = request.GET.get('callback', None)
        if cb:
            return '{0}({1})'.format(cb, data)

        return HttpResponse(data)

    def get_data(self, request, *args, **kwargs):
        query = self.query_from_request(request, *args, **kwargs)
        fields = self.fields_from_request(request)
        if self.find_one:
            result = self.collection.find_one(query, fields=fields)
        else:
            result = self.collection.find(query, fields=fields)
            sort = self.sort_from_request(request)
            if sort:
                result = result.sort(sort)

        return result

    def fields_from_request(self, request):
        fields = request.GET.get('fields')

        if not fields:
            return self.default_fields
        else:
            d = {field: 1 for field in fields.split(',')}
            d['_id'] = d.pop('id', 1)
            d['_type'] = 1
            return d

    def sort_from_request(self, request):
        return None

    def _clean(self, obj):
        if isinstance(obj, dict):
            if '_id' in obj:
                obj['id'] = obj['_id']

            for key, value in obj.items():
                if key.startswith('_'):
                    del obj[key]
                else:
                    obj[key] = self._clean(value)
        elif isinstance(obj, list):
            obj = [self._clean(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            obj = self._clean(obj.__dict__)

        return obj


class MetadataList(JsonView):
    collection = db.metadata
    default_fields = {'name': 1, 'feature_flags': 1, 'chambers': 1, '_id': 1}

    def query_from_request(self, request, *args):
        # always return all of them?
        return {}

    def sort_from_request(self, request):
        return 'name'


class MetadataDetail(JsonView):
    collection = db.metadata
    find_one = True

    def query_from_request(self, request, id):
        return {'_id': id}

