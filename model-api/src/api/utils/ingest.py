import re
from typing import Dict, List, Optional
import pandas as pd
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct,
    Filter, FieldCondition, MatchValue
)
import hashlib

CSV_FILE_PATH = 'data/sopi-2004-2024.csv'
COLLECTION = 'dairy_exports'
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
QDRANT_URL = "http://localhost:6333"

def load_and_transform(csv_path: str) -> pd.DataFrame:

    df = pd.read_csv(csv_path)

    year_cols = [c for c in df.columns if re.fullmatch(r'\d{4}', c)]
    base_cols = ['Diary export', 'Year to 30 June', 'Units']

    long_df = df.melt(id_vars=base_cols, value_vars=year_cols, var_name='Year', value_name='Value')

    def to_number(x: str) -> Optional[float]:
        x = x.strip()
        if x in ('', '-', 'NA', 'N/A'):
            return None
        return float(x.replace(',', ''))

    long_df['Value'] = long_df['Value'].apply(to_number)
    long_df.rename(columns={'Diary export': 'Product', 'Year to 30 June': 'Measure'} , inplace=True)

    def make_fact(row) -> str:
        product = row['Product']
        measure = row['Measure']
        units = row['Units']
        year = row['Year']
        value = row['Value']
        country = 'New Zealand'

        m = measure.lower()

        if m.startswith('average export price'):
            return f'In {year}, the average export price for {product} was {value} {units} in {country}.'
        elif m.startswith('export volume'):
            return f'In {year}, the export volume of {product} was {value} {units} in {country}.'
        elif m.startswith('export revenue'):
            return f'In {year}, the export revenue of {product} was {value} {units} in {country}.'
        else:
            return f'In {year}, the {measure} of {product} was {value} {units} in {country}.'
        
    long_df['fact_text'] = long_df.apply(make_fact, axis=1)
    long_df = long_df[long_df['fact_text'].str.strip() != '']
    return long_df

def deterministic_id(payload: Dict) -> str:
    '''
    Build a stable UUID5 from key fields so re-ingests update rather than duplicate.
    '''
    key = f'{payload.get('product')}|{payload.get('measure')}|{payload.get('units')}|{payload.get('year')}|{payload.get('amount_raw')}'
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))

def main():
    # 1) Prepare data
    long_df = load_and_transform(CSV_FILE_PATH)
    print(f"Transformed rows: {len(long_df)}")

    # 2) Embedding model
    model = SentenceTransformer(EMBED_MODEL)
    dim = model.get_sentence_embedding_dimension()

    # 3) Qdrant collection
    client = QdrantClient(url=QDRANT_URL)
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        # Optional: create payload schema via aliases or wait-on-write; Qdrant is schemaless for payload.

    # 4) Build points in batches
    points: List[PointStruct] = []
    BATCH = 256

    for i, row in long_df.iterrows():
        payload = {
            "product": row["Product"],
            "measure": row["Measure"],
            "units": row["Units"],
            "year": int(row["Year"]),
            "value": row["Value"],
            "amount": row["Value"],
            "fact_text": row["fact_text"],
            "tenant": "acme",
            "domain": "dairy_exports",
            "source": "csv",
            "mime_type": "text/csv",
        }
        pid = deterministic_id(payload)
        vec = model.encode(row["fact_text"]).tolist()
        points.append(PointStruct(id=pid, vector=vec, payload=payload))

        if len(points) >= BATCH:
            client.upsert(collection_name=COLLECTION, points=points)
            points = []

    if points:
        client.upsert(collection_name=COLLECTION, points=points)

    count = client.count(COLLECTION).count
    print(f"Collection '{COLLECTION}' now has {count} points.")

if __name__ == "__main__":
    main()
