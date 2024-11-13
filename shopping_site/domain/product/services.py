#shopping_site/domain/product/services.py

from shopping_site.domain.product.models import ProductFactory
from shopping_site.domain.product.models import Product
from typing import List,Type



class ProductService:
    """
    Service class responsible for handling product-related operations, such as product add,update,delete.
    """

    @staticmethod
    def get_product_factory() -> Type[ProductFactory]:
        """
        This method returns the ProductFactory class for creating users.
        """
        return ProductFactory
    
    @staticmethod
    def get_product_by_id(product_id: str) -> Product:
        """
        This method retrieves a user by their ID using the ProductRepository.
        """
        try:
            return Product.objects.get(id=product_id)  
        except Product.DoesNotExist:
            raise ValueError(f"Product with ID {product_id} does not exist.")
        
    @staticmethod
    def get_all_products():
        """
        This method retrieves all products.

        Returns:
            List[Product]: A list of all products in the database.
        """
        return Product.objects.all()

    @staticmethod
    def search_products(query: str) -> List[Product]:
        """
        This method searches for products based on the query string.

        Args:
            query (str): A keyword to search for in the product title.

        Returns:
            List[Product]: A list of products that match the search query.
        """
        return Product.objects.filter(title__icontains=query)