# shopping_site/application/product/services.py

from shopping_site.domain.product.services import ProductService
from shopping_site.domain.product.models import Product
from typing import Dict, List
from shopping_site.infrastructure.logger.models import AttributeLogger
from django.db.models import Q,Count
from django.db.models.expressions import Subquery

class ProductApplicationService:
    """
    Application service class responsible for handling the business logic
    related to product operations such as creating, updating, deleting,
    and filtering products.
    """

    
    def __init__(self, log: AttributeLogger) -> None:
        self.log = log  # Store the logger instance

    
    def create_product(self, data: Dict) -> Product:
        """
        Creates a new product using the provided data.
        
        Args:
            data (dict): The data used to create the product.

        Returns:
            Product: The newly created product or an error message if failed.
        """
        try:
            # Log the creation attempt
            self.log.info(f"Attempting to create product with title: {data['title']}")
            
            # Proceed to create the new product if no duplicate found
            product_factory = ProductService.get_product_factory()
            product = product_factory.build_entity_with_id(
                title=data["title"],
                description=data["description"],
                price=data["price"],
                quantity=data["quantity"],
                image=data["image"]
            )
            
            product.save()
            self.log.info(f"Product with title '{data['title']}' created successfully (ID: {product.id})")
            return product

        except Exception as e:
            self.log.error(f"Error creating product: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"
        


    @staticmethod
    def get_product_by_id(product_id: str) -> Product:
        """
        Retrieves a product by its ID.
        
        Args:
            product_id (str): The ID of the product to retrieve.
        
        Returns:
            Product: The product corresponding to the given ID.
        
        Raises:
            ValueError: If the product is not found.
        """
        product = ProductService.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        return product
    
    @staticmethod
    def get_product_by_id_id(product_id: str) -> Product:
        """
        Retrieves a product by its ID.
        
        Args:
            product_id (str): The ID of the product to retrieve.
        
        Returns:
            Product: The product corresponding to the given ID.
        
        Raises:
            ValueError: If the product is not found.
        """
        product = ProductService.get_product_by_id_id(product_id)
        if not product:
            raise ValueError("Product not found")
        return product
    


    @staticmethod
    def update_product(product_id: str, data: Dict) -> Product:
        """
        Updates an existing product with the provided data.
        
        Args:
            product_id (str): The ID of the product to update.
            data (dict): The updated data for the product.

        Returns:
            Product: The updated product.
        """
        
        product = ProductService.get_product_by_id(product_id)
        for key, value in data.items():
            setattr(product, key, value)
        product.save()
        return product

    @staticmethod
    def delete_product(product_id: str) -> bool:
        """
        Deletes the product with the provided ID.
        
        Args:
            product_id (str): The ID of the product to delete.

        Returns:
            bool: True if the product was deleted successfully.
        """
        try:
            product = ProductService.get_product_by_id(product_id)
            product.delete()
            return True
        except ValueError:
            return False

    
    def get_all_products(self) -> List[Product]:
        """
        Retrieves all products, applying any business logic if needed.
        
        Returns:
            List[Product]: A list of all products in the database.
        
        Raises:
            Exception: If an error occurs during the retrieval of products.
        """
        try:
            self.log.info("Attempting to retrieve all products from the database.")
            products = ProductService.get_all_products()
            self.log.info(f"Successfully retrieved {len(products)} products from the database.")
            return products

        except Exception as e:
            # Log the error in case of failure
            self.log.error(f"Error retrieving products: {str(e)}")
            raise Exception(f"An error occurred while retrieving products: {str(e)}")

    @staticmethod
    def search_products(query: str) -> List[Product]:
        """
        Searches for products based on the query, applying any business rules.
        
        Args:
            query (str): A search query for the product title.

        Returns:
            List[Product]: A list of products that match the search query.
        """
        return ProductService.search_products(query)
    

    # def filter_products(self, search_query: str, min_price: int = None, max_price: int = None):
    #     """
    #     Filters products based on the search query. Searches by title and description.
    #     Optionally filters by price range if min_price or max_price are provided.
    #     If both search query and price filters are provided, applies both conditions.
    #     """
    #     try:
    #         # Start with the base query for title and description search
    #         query = Q(title__icontains=search_query) | Q(description__icontains=search_query)

    #         # Apply price filters if provided (using ternary-like logic)
    #         if min_price:
    #             query &= Q(price__gte=min_price)  # Filter for price greater than or equal to min_price

    #         if max_price:
    #             query &= Q(price__lte=max_price)  # Filter for price less than or equal to max_price

    #         # Perform the filter with the combined query
    #         filtered_products = Product.objects.filter(query).order_by("id")

    #         return filtered_products
    #     except Exception as e:
    #         self.log.error(f"Error filtering products: {str(e)}")
    #         raise e



    def filter_products(self, search_query: str, min_price: int = None, max_price: int = None):
        """
        Filters products based on the search query and price range. It combines both the product fetch and 
        count operations in a single query.
        """
        try:
            # Start with the base query for title and description search
            query = Q(title__icontains=search_query) | Q(description__icontains=search_query)

            if min_price:
                query &= Q(price__gte=min_price) 

            if max_price:
                query &= Q(price__lte=max_price) 
        
            products = Product.objects.filter(query).order_by('id') \
                .annotate(
                    total_count=Subquery(
                        Product.objects.filter(query).values('id').annotate(count=Count('id')).values('count')[:1]
                    ))
                # )[(page - 1) * page_size:page * page_size]

       
            # total_count = products[0].total_count if products else 0

            # print('products : ',products,'total count',total_count)
            return products

        except Exception as e:
            self.log.error(f"Error filtering products: {str(e)}")
            raise e


