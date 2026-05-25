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
    #"weather": r"D:\University\ThirdYear\BakalauraDarbs\code\data\data.grib",
    "relatedness_cache": os.path.join(CSV_DIR,"relatedness_cache.csv"),
    "iteration": os.path.join(CSV_DIR,"shop_Weather"),
    "data_collection":os.path.join(CSV_DIR, "scenario100_data_best.csv"),
    "data_collection_curr":os.path.join(CSV_DIR, "scenario100_data_curr.csv"),
    "data_collection_new":os.path.join(CSV_DIR,"scenario100_data_new.csv"),

    #"data_collection": r"D:\University\ThirdYear\BakalauraDarbs\code\data_best_shop_Weather.csv",
    #"data_collection_curr": r"D:\University\ThirdYear\BakalauraDarbs\code\data_curr_shop_Weather.csv",
    #"data_collection_new": r"D:\University\ThirdYear\BakalauraDarbs\code\data_new_shop_Weather.csv"



    #"taskFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\extraSmallTasks_offset.csv",
    #"technicianFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\extraSmallTech_offset.csv",
    #"taskFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\smallTaskDatasetIncome2_offset.csv",
    #"technicianFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\smallTechnicianDatasetIncome2_offset.csv",
    #"shopFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\shops_filtered2_offset.csv",
    #"depotFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\depoDataset_offset.csv",
    #"distances": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\distances.csv",
    
    #"weather_cahce": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\weather_cache.csv",


    # Previous alternatives (commented out)
    # "taskFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\data\8Instances\25886 sdsdfsdfdssds dfsfsdasdfs3245opm sdsd707\computational_task_year_2022_instance_0.csv"
    # "technicianFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\data\8Instances\25886707\computational_technician_year_2022_instance_0.csv"
    # "taskFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\smallTaskDatasetIncomeBIIG2.csv"
    # "technicianFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\smallTechnicianDatasetIncomeBIIG2.csv"
    # "taskFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\smallTaskDatasetIncomeBIIG_offset.csv"
    # "technicianFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\smallTechnicianDatasetIncomeBIIG2_offset.csv"
    # "taskFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\smallTaskDatasetIncomeMIID_offset copy.csv"
    # "technicianFilePath": r"D:\University\ThirdYear\BakalauraDarbs\code\dataGeneration\offset\smallTechnicianDatasetIncomeMIID2_offset copy.csv"
}