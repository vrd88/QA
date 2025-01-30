from pymilvus import connections, Collection
import pandas as pd
from sqlalchemy import create_engine

connections.connect(alias="default", host="localhost", port="19530")

# Specify the collection name
collection_name = "QC_Collection_3"
collection = Collection(name=collection_name)
collection.load()

batch_size = 1000
offset = 0
all_data = []

while True:
    results = collection.query(
        expr="",
        output_fields=["source", "file_name", "page", "text", "pk"],
        offset=offset,
        limit=batch_size
    )
    if not results:
        break
    all_data.extend(results)
    offset += batch_size

df = pd.DataFrame(all_data)
engine = create_engine('sqlite:///exported_collection.db')
df.to_sql('QC_Collection_3', con=engine, if_exists='replace', index=False)

print("Data exported to 'exported_collection.db' in the 'QC_Collection_3' table.")
