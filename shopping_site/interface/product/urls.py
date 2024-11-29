# shopping_site/interface/product/urls

from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    ProductSearchView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    ProductManageView,
)

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("product/<uuid:product_id>/", ProductDetailView.as_view(), name="product_detail"),
    path("search/", ProductSearchView.as_view(), name="product_search"),
    path("create/", ProductCreateView.as_view(), name="product_create"),
    path("product/manage/", ProductManageView.as_view(), name="product_manage"),
    path("update/<uuid:product_id>/", ProductUpdateView.as_view(), name="product_update"),
    path("delete/<uuid:product_id>/", ProductDeleteView.as_view(), name="product_delete"),
]
