# shopping_site/interface/product/views.py
from django.shortcuts import render,redirect
from shopping_site.application.product.services import ProductApplicationService
from .forms import ProductForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.db import IntegrityError
from django.http import JsonResponse
from django.views import View
from shopping_site.infrastructure.logger.models import logger
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class ProductCreateView(FormView):
    """
    Create a new product using Django's FormView.
    """

    form_class = ProductForm
    template_name = 'product_create.html'
    success_url = reverse_lazy('product_list')  
    product_service=ProductApplicationService(log=logger)

    def form_valid(self, form):
        try:
            # Create product using the application service
            product_data = form.cleaned_data
            product=self.product_service.create_product(product_data)
            if isinstance(product, str):  # If the returned value is a string (error message)
                # Add the error message to the form
                form.add_error('title', product)
                return self.form_invalid(form)
            messages.success(self.request, "Product added successfully!")
            return super().form_valid(form)
        except IntegrityError as e:
            # Handle specific database integrity issues, like duplicate entries
            messages.error(self.request, "Error creating product. Please try again.")
            return self.form_invalid(form)
        except Exception as e:
            # Handle any other unexpected errors
            messages.error(self.request, f"An unexpected error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Handle invalid form (e.g., form errors) and re-render the page with errors
        messages.error(self.request, "There were errors with the form. Please check and try again.")
        return super().form_invalid(form)


class ProductListView(FormView):

    """
    List all products with an optional form for filtering.
    """
    form_class = ProductForm  # Use this if you want filtering functionality
    template_name = 'product_list.html'
    success_url = reverse_lazy('product_list')
    product_service = ProductApplicationService(log=logger)

    def get(self, request, *args, **kwargs):
        try:
            # Get filter parameters from the GET request
            search_query = request.GET.get('search_query', '')
            min_price = request.GET.get('min_price', None)
            max_price = request.GET.get('max_price', None)
         

            if min_price:
                try:
                    min_price = float(min_price)
                except ValueError:
                    min_price = None  # If invalid, reset to None

            if max_price:
                try:
                    max_price = float(max_price)
                except ValueError:
                    max_price = None  # If invalid, reset to None

            product_data = self.product_service.filter_products(
                search_query=search_query,
                min_price=min_price,
                max_price=max_price,
             
            )

            logger.info(f"Filtered products with query: {search_query}, min_price: {min_price}, max_price: {max_price}")

            product_data = product_data.order_by('id')
            paginator = Paginator(product_data, 9)  # Show 9 products per page
            page = request.GET.get('page', 1)

            try:
                products = paginator.page(page)
            except PageNotAnInteger:
                products = paginator.page(1)
            except EmptyPage:
                products = paginator.page(paginator.num_pages)

           

            return render(request, self.template_name, {
                'product_data': products,
                'search_query': search_query,
                'min_price': min_price,
                'max_price': max_price,
         
            })
           
        except Exception as e:
            logger.error(f"Error occurred while fetching products: {str(e)}")
            return render(request, self.template_name, {'error_message': "An error occurred while fetching products."})
        

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


class ProductDetailView(View):
    """
    View for displaying a single product's details.
    """
    def get(self, request, product_id):
        product = ProductApplicationService.get_product_by_id(product_id)
        if product is None:
            return render(request, '404.html', status=404)
        return render(request, 'product_detail.html', {'product': product})
    

class ProductDeleteView(View):
    """
    View for deleting a product.
    """
    def post(self, request, product_id):
        success = ProductApplicationService.delete_product(product_id)
        if success:
            return redirect('product_list')
        return render(request, '404.html', status=404)
