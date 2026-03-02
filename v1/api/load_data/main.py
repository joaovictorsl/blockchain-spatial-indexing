import os

if __name__ == "__main__":
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "mongo")
    if STORAGE_TYPE == "mongo":
        from load_mongo import load_geojson_data
    else:
        from load_psql import load_geojson_data

    load_geojson_data()
