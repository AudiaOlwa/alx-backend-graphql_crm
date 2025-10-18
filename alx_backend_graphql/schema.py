import graphene
from crm.schema import CRMQuery  # ✅ importe CRMQuery depuis ton app CRM

class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

schema = graphene.Schema(query=Query)
