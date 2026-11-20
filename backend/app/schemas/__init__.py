"""API schemas: the shapes of JSON requests and responses (Pydantic)

Kept separate from the database models because the API and the tables change
for different reasons. For instance: responses include "stock",
which is not a column in the schema. So the API response has a stock field,
but the database does not, only events rows it's derived from.

"""
