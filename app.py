from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'mysecretkey'  # Required for flash messages

# Connect to MongoDB (adjust host/port if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client["militaryDB"]

# Dictionary defining each collection and its fields
collections_info = {
    "personnel": {
        "display_name": "Personnel Information",
        "fields": ["personnel_id", "name", "age", "rank", "unit"]
    },
    "units": {
        "display_name": "Units",
        "fields": ["unit_id", "unit_name", "location", "commander"]
    },
    "weapons": {
        "display_name": "Weapons",
        "fields": ["weapon_id", "weapon_name", "type", "status"]
    },
    "missions": {
        "display_name": "Missions",
        "fields": ["mission_id", "mission_name", "objective", "status"]
    },
    "vehicles": {
        "display_name": "Vehicles",
        "fields": ["vehicle_id", "vehicle_name", "type", "status"]
    }
}

# Home Page: Displays 5 buttons (one for each "table"/collection)
@app.route('/')
def home():
    return render_template('index.html', collections_info=collections_info)

# Form Page: Allows user to insert data into the chosen collection
@app.route('/form/<collection_key>', methods=['GET', 'POST'])
def form_page(collection_key):
    if collection_key not in collections_info:
        return "Invalid Collection Key!", 404

    collection_data = collections_info[collection_key]
    collection = db[collection_key]  # The actual MongoDB collection

    if request.method == 'POST':
        # Build a document from the form input
        doc = {}
        for field in collection_data["fields"]:
            doc[field] = request.form.get(field, "")

        # Insert into MongoDB
        collection.insert_one(doc)

        flash(f"Data inserted into {collection_data['display_name']} successfully!", "success")
        return redirect(url_for('success'))

    return render_template(
        'form.html',
        collection_key=collection_key,
        collection_data=collection_data
    )

# Success Page: Shown after data is inserted
@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
