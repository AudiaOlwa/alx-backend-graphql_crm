import re
from graphene import relay
from django.db import transaction
from django.utils import timezone
import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
#from .filters import CustomerFilterInput, ProductFilterInput, OrderFilterInput
from crm.models import Product, Customer, Order
from crm.filters import CustomerFilter, ProductFilter, OrderFilter


# ==========================================================
# Object Types
# ==========================================================
class CustomerType(DjangoObjectType):
    createdAt = graphene.DateTime(source='created_at')
    class Meta:
        model = Customer
#        interfaces = (graphene.relay.Node,)
        interfaces = (relay.Node,)
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = ("id", "customer", "products", "total_amount", "order_date")


# ==========================================================
# Input Types
# ==========================================================
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(required=False, default_value=0)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)


# ==========================================================
# Utility: Validation helpers
# ==========================================================
def validate_email_unique(email):
    if Customer.objects.filter(email=email).exists():
        raise ValueError("Email already exists.")


def validate_phone_format(phone):
    if phone and not re.match(r"^(\+\d{7,15}|\d{3}-\d{3}-\d{4})$", phone):
        raise ValueError("Invalid phone number format.")


# ==========================================================
# Mutations
# ==========================================================

# ---- CreateCustomer ----
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        try:
            validate_email_unique(input.email)
            validate_phone_format(input.phone)

            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone
            )
            customer.save()
            return CreateCustomer(customer=customer, message="Customer created successfully.")
        except ValueError as e:
            return CreateCustomer(customer=None, message=str(e))


# ---- BulkCreateCustomers ----
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input):
        created_customers = []
        errors = []

        with transaction.atomic():
            for cust in input:
                try:
                    validate_email_unique(cust.email)
                    validate_phone_format(cust.phone)
                    customer = Customer.objects.create(
                        name=cust.name,
                        email=cust.email,
                        phone=cust.phone
                    )
                    created_customers.append(customer)
                except ValueError as e:
                    errors.append(f"{cust.email}: {str(e)}")
                except Exception as e:
                    errors.append(f"{cust.email}: Unexpected error ({e})")

        return BulkCreateCustomers(customers=created_customers, errors=errors)


# ---- CreateProduct ----
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        if input.price <= 0:
            return CreateProduct(product=None, message="Price must be positive.")
        if input.stock < 0:
            return CreateProduct(product=None, message="Stock cannot be negative.")

        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock or 0
        )
        return CreateProduct(product=product, message="Product created successfully.")


# ---- CreateOrder ----
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(order=None, message="Invalid customer ID.")

        if not input.product_ids:
            return CreateOrder(order=None, message="At least one product must be provided.")

        products = list(Product.objects.filter(id__in=input.product_ids))
        if len(products) != len(input.product_ids):
            return CreateOrder(order=None, message="Some product IDs are invalid.")

        total_amount = sum(p.price for p in products)
        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=input.order_date or timezone.now()
        )
        order.products.set(products)

        return CreateOrder(order=order, message="Order created successfully.")


# ==========================================================
# Root Mutation Class
# ==========================================================
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


# ==========================================================
# Root Query (can be simple)
# ==========================================================
# --- QUERY ---
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        order_by=graphene.String()
    )
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        order_by=graphene.String()
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        order_by=graphene.String()
    )


    customers_count = graphene.Int()
    orders_count = graphene.Int()
    total_revenue = graphene.Float()

    def resolve_customers_count(self, info):
        return Customer.objects.count()

    def resolve_orders_count(self, info):
        return Order.objects.count()

    def resolve_total_revenue(self, info):
        return Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        
    # --- resolvers ---
    def resolve_all_customers(self, info, filter=None, order_by=None):
        qs = Customer.objects.all()
        if filter:
            if filter.get("nameIcontains"):
                qs = qs.filter(name__icontains=filter["nameIcontains"])
            if filter.get("emailIcontains"):
                qs = qs.filter(email__icontains=filter["emailIcontains"])
            if filter.get("createdAtGte"):
                qs = qs.filter(created_at__gte=filter["createdAtGte"])
            if filter.get("createdAtLte"):
                qs = qs.filter(created_at__lte=filter["createdAtLte"])
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_products(self, info, filter=None, order_by=None):
        qs = Product.objects.all()
        if filter:
            if filter.get("nameIcontains"):
                qs = qs.filter(name__icontains=filter["nameIcontains"])
            if filter.get("priceGte"):
                qs = qs.filter(price__gte=filter["priceGte"])
            if filter.get("priceLte"):
                qs = qs.filter(price__lte=filter["priceLte"])
            if filter.get("stockGte"):
                qs = qs.filter(stock__gte=filter["stockGte"])
            if filter.get("stockLte"):
                qs = qs.filter(stock__lte=filter["stockLte"])
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_orders(self, info, filter=None, order_by=None):
        qs = Order.objects.all()
        if filter:
            if filter.get("totalAmountGte"):
                qs = qs.filter(total_amount__gte=filter["totalAmountGte"])
            if filter.get("totalAmountLte"):
                qs = qs.filter(total_amount__lte=filter["totalAmountLte"])
            if filter.get("orderDateGte"):
                qs = qs.filter(order_date__gte=filter["orderDateGte"])
            if filter.get("orderDateLte"):
                qs = qs.filter(order_date__lte=filter["orderDateLte"])
            if filter.get("customerName"):
                qs = qs.filter(customer__name__icontains=filter["customerName"])
            if filter.get("productName"):
                qs = qs.filter(products__name__icontains=filter["productName"])
        if order_by:
            qs = qs.order_by(order_by)
        return qs

#--------------------------

class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []

        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(product)

        message = f"{len(updated)} product(s) updated"
        return UpdateLowStockProducts(updated_products=updated, message=message)


class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()