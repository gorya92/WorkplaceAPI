from sqlalchemy import Table, Column, Integer, String, TIMESTAMP, MetaData, LargeBinary

metadata = MetaData()

images = Table(
    "images",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("date", TIMESTAMP),
    Column("image_data", LargeBinary),
)
