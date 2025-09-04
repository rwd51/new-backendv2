from collections import OrderedDict

from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.LimitOffsetPagination):
    def get_limit(self, request):
        limit = request.query_params.get(self.limit_query_param)
        if limit and limit.lower() == "all":
            return limit
        return super().get_limit(request)

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        self.count = self.get_count(queryset)
        self.offset = self.get_offset(request)
        self.request = request

        if self.limit == "all":
            self.limit = self.count

        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])

    def get_end_index(self):
        return min(self.offset + self.limit, self.count) - 1

    def get_start_index(self):
        return self.offset

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('start_index', self.get_start_index()),
            ('end_index', self.get_end_index()),
            ('results', data)
        ]))
