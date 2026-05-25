import os

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)

CSV_DIR = os.path.join(BASE_DIR, "csv")


urls = {
    "taskFilePath": os.path.join(CSV_DIR, "tasks.csv"),
    "technicianFilePath": os.path.join(CSV_DIR, "technicians.csv"),
    "shopFilePath": os.path.join(CSV_DIR, "shops.csv"),
    "depotFilePath": os.path.join(CSV_DIR, "depots.csv"),
    "distances":os.path.join(CSV_DIR, "distances_cache.csv"),
    "weather_cahce":os.path.join(CSV_DIR, "weather_cache.csv"),
    "geometry_cahce":os.path.join(CSV_DIR, "geometry_cache.csv"),
    "weather":os.path.join(CSV_DIR,"data.grib"),
    "relatedness_cache": os.path.join(CSV_DIR,"relatedness_cache.csv"),
    "iteration": os.path.join(CSV_DIR,"shop_Weather"),
    "data_collection":os.path.join(CSV_DIR, "scenario100_data_best.csv"),
    "data_collection_curr":os.path.join(CSV_DIR, "scenario100_data_curr.csv"),
    "data_collection_new":os.path.join(CSV_DIR,"scenario100_data_new.csv"),


}