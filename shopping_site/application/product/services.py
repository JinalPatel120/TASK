# shopping_site/application/product/services.py

from shopping_site.domain.product.services import ProductService
from shopping_site.domain.product.models import Product
from typing import Dict, List
from shopping_site.infrastructure.logger.models import AttributeLogger

class ProductApplicationService:
    """
    Application service class responsible for handling the business logic
    related to product operations such as creating, updating, deleting,
    and filtering products.
    """

    
    def __init__(self, log: AttributeLogger) -> None:
        self.log = log  # Store the logger instance

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

            # Check if a product with the same title already exists
            if Product.objects.filter(title=data["title"]).exists():
                error_message = f"A product with the title '{data['title']}' already exists."
                self.log.warning(error_message) 
                return error_message
            
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
    
    def filter_products(self, search_query: str):
        """
        Filters products based on the search query. Searches by title and description.
        """
        try:
            # Perform the search by matching the search query in product title or description
            filtered_products = Product.objects.filter(
                title__icontains=search_query
            ) | Product.objects.filter(
                description__icontains=search_query
            )

            return filtered_products
        except Exception as e:
            self.log.error(f"Error filtering products: {str(e)}")
            raise
