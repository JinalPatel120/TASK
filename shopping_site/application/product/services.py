# shopping_site/application/product/services.py

from shopping_site.domain.product.services import ProductService
from shopping_site.domain.product.models import Product
from typing import Dict, List


class ProductApplicationService:
    """
    Application service class responsible for handling the business logic
    related to product operations such as creating, updating, deleting,
    and filtering products.
    """

    @staticmethod
    def create_product(data: Dict) -> Product:
        """
        Creates a new product using the provided data.
        
        Args:
            data (dict): The data used to create the product.

        Returns:
            Product: The newly created product.
        """
        # You can apply any business rules here before creating the product.
        product_factory = ProductService.get_product_factory()
        product = product_factory.create(**data)
        product.save()
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

    @staticmethod
    def get_all_products() -> List[Product]:
        """
        Retrieves all products, applying any business logic if needed.
        
        Returns:
            List[Product]: A list of all products in the database.
        """
        return ProductService.get_all_products()

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
