from django.core.paginator import Paginator, EmptyPage
from restless.modelviews import ListEndpoint, DetailEndpoint
from restless.models import serialize
from restless.http import HttpError, Http200


class PublicListEndpoint(ListEndpoint):
    methods = ['GET']
    per_page = 100
    serialize_config = {}
    default_fields = []

    def adjust_filters(self, params):
        return params

    def filter(self, data, **kwargs):
        kwargs = self.adjust_filters(kwargs)
        return data.filter(**kwargs)

    def sort(self, data, sort_by):
        return data.order_by(*sort_by)

    def paginate(self, data, page):
        paginator = Paginator(data, per_page=self.per_page)
        return paginator.page(page)

    def get(self, request, *args, **kwargs):
        params = request.params
        page = 1
        if 'page' in params:
            page = int(params.pop('page'))

        sort_by = []
        if 'sort_by' in params:
            sort_by = params.pop('sort_by').split(",")

        if '_' in params:
            params.pop("_")

        fields = self.default_fields
        if 'fields' in params:
            fields = params.pop('fields').split(",")

        callback = None
        if 'callback' in params:
            callback = params.pop('callback')

        data = self.get_query_set(request, *args, **kwargs)
        data = self.filter(data, **params)
        data = self.sort(data, sort_by)
        try:
            data_page = self.paginate(data, page)
        except EmptyPage:
            raise HttpError(
                404,
                'No such page (heh, literally - its out of bounds)'
            )

        response = Http200({
            "meta": {
                "count": len(data_page.object_list),
                "page": page,
                "per_page": self.per_page,
                "max_page": data_page.end_index(),
                "total_count": data.count(),
            },
            "results": [
                serialize(x, **self.get_serialize_config(fields=fields))
                for x in data_page.object_list
            ]
        })

        if callback:
            # If we have a callback, let's wrap the content in a jsonp
            # callback.
            response.content = (
                callback.encode() + b"("
                    + response.content
                + b");"
            )

        return response

    @classmethod
    def get_serialize_config(cls, fields=None):
        if fields is None:
            fields = cls.default_fields

        r = {
            "fields": [
                (x, cls.serialize_config[x]) for x in fields
            ]
        }
        return r


class PublicDetailEndpoint(DetailEndpoint):
    methods = ['GET']
