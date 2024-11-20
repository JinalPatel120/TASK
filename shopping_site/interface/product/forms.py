from django import forms
from shopping_site.domain.product.models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'quantity', 'image']
    
    # Title Validation
    def clean_title(self):
        title = self.cleaned_data.get('title')
        
        if not title:
            raise forms.ValidationError("Product title is required.")
        
        if len(title) > 20:  
            raise forms.ValidationError("Product title must not exceed 20 characters.")
        
        if Product.objects.filter(title__iexact=title).exists():
            raise forms.ValidationError("A product with this title already exists.")
        
        return title
    
    # Description Validation
    def clean_description(self):
        description = self.cleaned_data.get('description')
        
        if not description:
            raise forms.ValidationError("Product description is required.")
        
        if len(description) < 10:  # Minimum length for the description
            raise forms.ValidationError("Description should be at least 10 characters long.")
        
        return description

    
    # Price Validation
    def clean_price(self):
        price = self.cleaned_data.get('price')
        
        if price is None:
            raise forms.ValidationError("Price is required.")
        elif price <= 0:
            raise forms.ValidationError("Price must be a positive number.")
        
        return price

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity') 
        if quantity is None:
            raise forms.ValidationError('Quantity cannot be empty.')
        elif quantity <= 0:
            raise forms.ValidationError('Quantity must be a positive integer.')

        return quantity

 
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise forms.ValidationError("Product image is required.")
          
        return image
    

class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'quantity', 'image']

    def clean_quantity(self):
        # Custom validation: Ensure the quantity is not greater than the available stock
        quantity = self.cleaned_data.get('quantity')
        product_id = self.instance.id
        product = Product.objects.get(id=product_id)

        if quantity > product.quantity:
            raise forms.ValidationError(f"Stock is not available. The maximum quantity you can order is {product.quantity}.")
        return quantity