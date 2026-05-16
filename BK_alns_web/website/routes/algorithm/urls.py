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
    "weather": r"",
    "relatedness_cache": r"",
    "iteration": "",
    "data_collection": r"D",
    "data_collection_curr": r"",
    "data_collection_new": r""

}
