from dataclasses import dataclass
import uuid
from django.db import models
from shopping_site.utils.custom_models import TimestampedModel


@dataclass(frozen=True)
class ProductID:
    """
    This is a value object that should be used to generate and pass the ProductID to the ProductFactory.
    """
    value: uuid.UUID


# ----------------------------------------------------------------------
# Product Model
# ----------------------------------------------------------------------

class Product(TimestampedModel):
    """
    Represents a Product model in the Domain Layer.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    title = models.CharField(max_length=150, unique=True, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    price = models.DecimalField(max_digits=10, blank=True,decimal_places=4)
    quantity = models.IntegerField( blank=True)
    image=models.ImageField(upload_to='product_image')

    class Meta:
        db_table = "product"

class ProductFactory:
    """ 
    Factory class for creating Product entities.
    """
    product_db={}

    @classmethod
    def build_entity_with_id(
        cls,
        title:str,
        description:str,
        price:int,
        quantity:int,
        image:str
    ) -> Product:
        """
        This is a factory method used for building an instance of Product.
        A ProductID is created when building the entity.
        """
        entity_id=ProductID(uuid.uuid4())
        return cls.build_entity(
            id=entity_id,
            title=title,
            description=description,
            price=price,
            quantity=quantity,
            image=image
        )
    
    @staticmethod
    def build_entity(
        id:ProductID,
        title:str,
        description:str,
        price:int,
        quantity:int,
        image:str
    ) -> Product:
        """
        This method creates a Product entity using the provided fields.
        """
        return Product(
            id=id.value,
            title=title,
            description=description,
            price=price,
            quantity=quantity,
            image=image
        )
        
    