from rest_framework.pagination import PageNumberPagination


class OfferPagination(PageNumberPagination):
    """Paging for the offer list, page size adjustable up to a ceiling."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
