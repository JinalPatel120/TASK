# shopping_site/interface/product/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from shopping_site.application.product.services import ProductApplicationService



class ProductListView(View):
    """
    List all products.
    """

    def get(self, request):
        products = ProductApplicationService.get_all_products()
        product_data = [{"id": product.id, "title": product.title, "price": product.price} for product in products]
        return render(request,'product_list.html',{'product_data':product_data})


class ProductCreateView(View):
    """
    Create a new product.
    """

    def post(self, request):
        data = request.POST
        product_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "price": data.get("price"),
            "quantity": data.get("quantity"),
            "image": data.get("image")
        }
        product = ProductApplicationService.create_product(product_data)
        return JsonResponse({"product_id": product.id}, status=201)


class ProductUpdateView(View):
    """
    Update an existing product.
    """
    def get(self, request, product_id):
        product = ProductApplicationService.get_product_by_id(product_id)
        product_data = {
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "quantity": product.quantity,
            "image": product.image
        }
        return render(request, 'product_update.html', {'product_data': product_data})

    def post(self, request, product_id):
        data = request.POST
        product_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "price": data.get("price"),
            "quantity": data.get("quantity"),
            "image": data.get("image")
        }
        try:
            product = ProductApplicationService.update_product(product_id, product_data)
            return JsonResponse({"product_id": product.id}, status=200)
        except ValueError:
            return JsonResponse({"error": "Product not found"}, status=404)

class ProductSearchView(View):
    """
    Search for products by title.
    """
    def get(self, request):
        query = request.GET.get("query", "")
        products = ProductApplicationService.search_products(query)
        product_data = [{"id": product.id, "title": product.title, "price": product.price} for product in products]
        return JsonResponse({"products": product_data}, status=200)
