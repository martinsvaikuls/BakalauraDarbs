programmas uzsākšanai termināli nepieciešams ievadīt "py -3.13 BK_proj/website/app.py"

rindas 42-44:
noliktavu faktors:  DEPOT_TEST = True 
veikalu faktors: SHOP_TEST = True
laikapstākļu faktors: WEATHER_TEST = True
ALNS optimizācijas algoritms: https://github.com/martinsvaikuls/BakalauraDarbs/blob/main/BK_alns_web/website/routes/algorithm/alns.py

# DATI

Lietoto datu kopu atsauces:

| Modificēts no (Nielsen & Pisinger, 2024) |
 technicians.csv,
 tasks.csv |
 
| Modificēts no (Overpass turbo, n.d.). |
 shops.csv |

 
mapē "csv" nepieciešams ievietot laikapstākļu datni "data.grib", bakalaura darba eksperimentos tika lietota (Hersbach u.c. 2023)

papildus nepieciešami Latvijas ģeogrāfiskie ceļu dati no OpenStreetMap (n.d.)
ģeogrāfiskos datus nepieciešams sniegt kā internet pakalpojumu adresē "http://localhost:5000" vai arī aizvietot osrm_service.py OSRM_URL ar pieejamu OSMR lietojumprogrammu saskarni

# IZMANTOTIE INFORMĀCIJAS AVOTI

Hersbach, H., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz Sabater, J., Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A., Soci, C., Dee, D., Thépaut, J-N. (2023): ERA5 hourly data on single levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS), DOI: 10.24381/cds.adbb2d47 [viewed 2026-05-09]

Nielsen, C. C., & Pisinger, D. (2024). Technician and Task instances for a Dynamic Technician Routing and Scheduling problem (Version 1). Technical University of Denmark. https://doi.org/10.11583/DTU.25886707.v1 [viewed 2026-02-23]

OpenStreetMap. (n.d.). OpenStreetMap data extract for Latvia. Geofabrik. Retrieved from https://download.geofabrik.de/europe/latvia.html [viewed 2026-05-06]

Overpass turbo. (n.d.). Web-based data mining tool for OpenStreetMap. Retrieved from https://overpass-turbo.eu/ [viewed 2026-05-06]
