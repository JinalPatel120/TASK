# shopping_site/interface/product/views.py
from typing import Optional
from django.shortcuts import render, redirect
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
from django.contrib.auth.mixins import UserPassesTestMixin,LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.files.storage import FileSystemStorage
from django.db import DataError

def float_parser(value: Optional[float]) -> Optional[float]:
    if value:
        try:
            return float(value)
        except ValueError:
            return None  # If invalid, reset to None





class ProductListView(FormView):
    """
    List all products with an optional form for filtering.
    """

    form_class = ProductForm  # Use this if you want filtering functionality
    template_name = "product_list.html"
    success_url = "product_list"
    product_service = ProductApplicationService(log=logger)

    def get(self, request, *args, **kwargs):
        try:

            # Get filter parameters from the GET request
            search_query = request.GET.get("search_query", "")
            min_price = float_parser(request.GET.get("min_price", None))
            max_price = float_parser(request.GET.get("max_price", None))

            product_data = self.product_service.filter_products(
                search_query=search_query,
                min_price=min_price,
                max_price=max_price,
                # page=int(request.GET.get("page", 1)),  # Get the current page from the request
                # page_size=9,
            )

            logger.info(
                f"Filtered products with query: {search_query}, min_price: {min_price}, max_price: {max_price}"
            )

            paginator = Paginator(product_data, 9)
            page = request.GET.get("page", 1)

            try:
                products = paginator.page(page)
            except PageNotAnInteger:
                products = paginator.page(1)
            except EmptyPage:
                products = paginator.page(paginator.num_pages)

            return render(
                request,
                self.template_name,
                {
                    "product_data": products,
                    "search_query": search_query,
                    "min_price": min_price,
                    "max_price": max_price,
                    # "total_count": total_count,
                },
            )

        except Exception as e:
            logger.error(f"Error occurred while fetching products: {str(e)}")
            return render(
                request,
                self.template_name,
                {"error_message": "An error occurred while fetching products."},
            )


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only superusers can access the view."""
    
    def test_func(self):

        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):

            messages.error(self.request, "You must be an admin to access this page.")
            return redirect('login')  # Redirect to login page or another page if needed
        

class ProductCreateView(SuperuserRequiredMixin,FormView):
    """
    Create a new product using Django's FormView.
    """

    form_class = ProductForm
    template_name = "product_create.html"
    success_url = reverse_lazy("product_manage")
    product_service = ProductApplicationService(log=logger)

    def form_valid(self, form):
        try:
            # Create product using the application service
            product_data = form.cleaned_data
            product = self.product_service.create_product(product_data)
            if isinstance(
                product, str
            ):  # If the returned value is a string (error message)
                # Add the error message to the form
                form.add_error("title", product)
                return self.form_invalid(form)
            messages.success(self.request, "Product added successfully!")
            return super().form_valid(form)
        except IntegrityError as e:
            self.product_service.log.error(f"IntegrityError: {str(e)}")
            messages.error(self.request, "Error creating product. Please try again.")
            return self.form_invalid(form)
        except Exception as e:
            # Handle any other unexpected errors
            messages.error(self.request, f"An unexpected error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There were errors with the form. Please check and try again."
        )
        return super().form_invalid(form)


class ProductManageView(SuperuserRequiredMixin,View):
    """
    View to display a list of products with options to remove, edit, or manage stock.
    """

    product_service=ProductApplicationService(log=logger)
    def get(self, request):
        search_query = request.GET.get("search_query", "")
        min_price = float_parser(request.GET.get("min_price", None))
        max_price = float_parser(request.GET.get("max_price", None))

        try:
            product_data = self.product_service.filter_products(
                search_query=search_query,
                min_price=min_price,
                max_price=max_price,
            )

            paginator = Paginator(product_data, 9)
            page = request.GET.get("page", 1)

            try:
                products = paginator.page(page)
            except PageNotAnInteger:
                products = paginator.page(1)
            except EmptyPage:
                products = paginator.page(paginator.num_pages)

            return render(
                request,
                'product_manage.html',
                {
                    'products': products,
                    'search_query': search_query,
                    'min_price': min_price,
                    'max_price': max_price,
                },
            )
        except Exception as e:
            logger.error(f"Error occurred while fetching products: {str(e)}")
            messages.error(request, "An error occurred while fetching products.")
       

    def post(self, request):
        # Handle actions like remove, edit, or manage stock
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')

        if action == 'remove':
            ProductApplicationService.delete_product(product_id)
            return redirect('product_manage')

        elif action == 'edit':
            return redirect('product_update', product_id=product_id)

        elif action == 'manage_stock':
            return redirect('product_manage', product_id=product_id)  
        return redirect('product_manage')


class ProductUpdateView(SuperuserRequiredMixin,View):
    product_service=ProductApplicationService(log=logger)
    """
    Update an existing product.
    """

    def get(self, request, product_id):
        product = self.product_service.get_product_by_id(product_id)
        product_data = {
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "quantity": product.quantity,
            "image": product.image,
        }
        return render(request, "product_update.html", {"product_data": product_data})


    def post(self, request, product_id):
        data = request.POST
        product_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "price": data.get("price"),
            "quantity": data.get("quantity"),
        }

        image = request.FILES.get("image")
        if image:
            fs = FileSystemStorage(location='shopping_site/interface/product/product_image')  
            filename = fs.save(image.name, image)
            product_data["image"] = fs.url(filename)  
        else:
            existing_image = request.POST.get("existing_image")  
            if existing_image:
                product_data["image"] = existing_image  # Retain the existing image path

        try:
            self.product_service.update_product(product_id, product_data)
         
            messages.success(self.request, "Product updated successfully.")
            return redirect('product_manage')
        except DataError:
            messages.error(request, "The price value is too large. Please enter a valid price.")
            return redirect('product_update', product_id=product_id)
        except ValueError:
            return JsonResponse({"error": "Product not found"}, status=404)



class ProductDeleteView(SuperuserRequiredMixin,View):
    product_service=ProductApplicationService(log=logger)
    """
    View for deleting a product.
    """
    def post(self, request, product_id):

        success = self.product_service.delete_product(product_id)
        if success:
            messages.success(self.request, "Product deleted successfully!")
            return redirect('product_manage')
        else:
            messages.error(self.request, "Error deleting product. Please try again.")
            return render(request, "product_manage.html", status=404)


class ProductSearchView(View):
    product_service=ProductApplicationService(log=logger)
    """
    Search for products by title.
    """

    def get(self, request):
        query = request.GET.get("query", "")
        products = self.product_service.search_products(query)
        product_data = [
            {"id": product.id, "title": product.title, "price": product.price}
            for product in products
        ]
        return JsonResponse({"products": product_data}, status=200)


class ProductDetailView(View):
    product_service=ProductApplicationService(log=logger)
    """
    View for displaying a single product's details.
    """

    def get(self, request, product_id):
        product = self.product_service.get_product_by_id(product_id)
        if product is None:
            return render(request, "product_list.html", status=404)
        return render(request, "product_detail.html", {"product": product})
