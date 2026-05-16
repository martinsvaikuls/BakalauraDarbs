import csv
import os
import ast
import datetime
import json

DATETIME_FIELDS = {
    "technicians": ["start_tw", "end_tw"],
    "tasks": ["start_tw", "end_tw", "created"],
    # depots and shops may not have datetime
}

JSON_FIELDS = {
    "technicians": ["skills", "resources"],
    "tasks": ["skills", "resources", "relevant_technician_ids"],
    # depots and shops if any
}

class CSVDB:
    def __init__(self, folder="csv"):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def _get_file(self, table_name):
        return os.path.join(self.folder, f"{table_name}.csv")
    
    def ensure_table(self, table_name, fields):
        file_path = self._get_file(table_name)
        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields, delimiter=';')
                writer.writeheader()


    def get_all(self, table_name):
        """Load CSV and convert JSON and datetime fields back to Python types"""
        file_path = self._get_file(table_name)
        if not os.path.exists(file_path):
            return []

        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            items = []
            for row in reader:
                new_row = {}
                for key, val in row.items():
                    if val is None:
                        new_row[key] = None
                        continue
                    # Convert JSON fields
                    if key in JSON_FIELDS.get(table_name, []):
                        try:
                            new_row[key] = json.loads(val)
                        except Exception:
                            new_row[key] = val  # fallback
                    # Convert datetime fields
                    elif key in DATETIME_FIELDS.get(table_name, []):
                        try:
                            new_row[key] = datetime.datetime.fromisoformat(val)
                        except Exception:
                            new_row[key] = val
                    else:
                        new_row[key] = val
                items.append(new_row)
        return items

    def get_by_id(self, table_name, id_field, id_value):
        all_rows = self.get_all(table_name)
        for row in all_rows:
            if str(row[id_field]) == str(id_value):
                return row
        return None

    def insert(self, table_name, row):
        """Insert a row, converting JSON fields to proper JSON string"""
        row_copy = row.copy()
        for key in row_copy:
            val = row_copy[key]
            if isinstance(val, (dict, list)):
                row_copy[key] = json.dumps(val)
            elif isinstance(val, datetime.datetime):
                row_copy[key] = val.isoformat()
        file_path = self._get_file(table_name)
        file_exists = os.path.exists(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row_copy.keys(), delimiter=';')
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_copy)

    def update(self, table_name, id_field, id_value, new_row):
        all_rows = self.get_all(table_name)
        updated = False
        for i, row in enumerate(all_rows):
            if str(row[id_field]) == str(id_value):
                all_rows[i] = new_row
                updated = True
                break
        if updated:
            file_path = self._get_file(table_name)
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=new_row.keys(), delimiter=';')
                writer.writeheader()
                for row in all_rows:
                    # Convert JSON & datetime
                    row_copy = row.copy()
                    for k, v in row_copy.items():
                        if isinstance(v, (dict, list)):
                            row_copy[k] = json.dumps(v)
                        elif isinstance(v, datetime.datetime):
                            row_copy[k] = v.isoformat()
                    writer.writerow(row_copy)

    def list_clients(self):
        return self.get_all("users")


    def get_client_by_email(self, email):
        email = email.strip().lower()
        for c in self.get_all("users"):
            if c.get("email", "").strip().lower() == email:
                return c
        return None


    def create_client(self, client_data):
        import uuid
        client_data["client_id"] = str(uuid.uuid4())
        
        # Enforce exact CSV field order
        row = {
            "client_id": client_data["client_id"],
            "client_name": client_data["client_name"],
            "email": client_data["email"],
            "hash_password": client_data["hash_password"]
        }
        
        self.insert("users", row)
        return row  # always return keys exactly as CSV
    
    def load_csv(self, object_type):
        filename = self._get_file(object_type)
        # Create empty file with headers if missing
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8", newline="") as f:
                if object_type == "technicians":
                    f.write("id;master_id;skills;start_tw;end_tw;home_lat;home_long;resources\n")
                elif object_type == "tasks":
                    f.write("id;priority;skills;duration;start_tw;end_tw;created;relevant_technician_ids;lat;long;resources;income\n")
                elif object_type == "depots":
                    f.write("id;resources;start_tw;end_tw;lat;long;\n")
                elif object_type == "shops":
                    f.write("id;resources;start_tw;end_tw;lat;long;\n")

        # Load CSV normally
        with open(filename, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=";")
            items = []
            for row in reader:
                clean_row = {}
                for key, val in row.items():
                    if key is None:
                        continue

                    # Convert empty strings to None
                    if val == "":
                        val = None

                    # Convert datetime fields to datetime objects, then to ISO string
                    if object_type in DATETIME_FIELDS and key in DATETIME_FIELDS[object_type]:
                        try:
                            val = datetime.datetime.fromisoformat(val).isoformat()
                        except Exception:
                            pass  # leave as-is if it fails

                    # Convert JSON fields to Python objects
                    if object_type in JSON_FIELDS and key in JSON_FIELDS[object_type]:
                        try:
                            if val is not None:
                                # ast.literal_eval handles both dicts and lists
                                val = ast.literal_eval(val)
                        except Exception:
                            pass

                    clean_row[key] = val
                items.append(clean_row)
        return items


        # Example for specific object type
    def list_technicians(self):
        return self.load_csv("technicians")

    def list_tasks(self):
        return self.load_csv("tasks")

    def list_shops(self):
        return self.load_csv("shops")

    def list_depots(self):
        return self.load_csv("depots")
    

    def delete(self, table_name, id_value):
        file_path = self._get_file(table_name)
        if not os.path.exists(file_path):
            return False

        import csv

        rows = []
        deleted = False
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=";")
            fieldnames = reader.fieldnames
            for row in reader:
                if str(row.get("id")) != str(id_value):
                    rows.append(row)
                else:
                    deleted = True

        if deleted:
            with open(file_path, "w", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                writer.writerows(rows)

        return deleted
