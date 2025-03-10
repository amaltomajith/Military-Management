from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "replace_with_your_secret_key"

# -----------------------------
# 1. CONNECT TO MONGODB
# -----------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["military_management"]

# -----------------------------
# 2. DEFINE CATEGORIES + FIELDS
# -----------------------------
collections_map = {
    "personnel": "personnel",
    "units": "units",
    "weapons": "weapons",
    "missions": "missions",
    "vehicles": "vehicles"
}

fields_map = {
    "personnel": ["name", "rank", "experience", "role", "department"],
    "units": ["unit_name", "location", "capacity", "specialization", "commander"],
    "weapons": ["name", "company", "damage", "rate_of_fire", "amount"],
    "missions": ["name", "objective", "location", "status", "commander"],
    "vehicles": ["model", "type", "capacity", "range", "crew_required"]
}

# -----------------------------
# 3. HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    """
    Shows the homepage with 5 buttons: Personnel, Units, Weapons, Missions, Vehicles.
    """
    return render_template("index.html")

# -----------------------------
# 4. COLLECTION ROUTE (VIEW + DELETE ONLY)
# -----------------------------
@app.route("/collection/<category>")
def show_collection(category):
    """
    GET: Display all documents in the category in a table.
         The 'Update' button now links to a separate page (/update/<category>/<doc_id>).
    """
    if category not in collections_map:
        return "Invalid category!", 404

    col_name = collections_map[category]
    col = db[col_name]

    documents = list(col.find())
    category_fields = fields_map[category]

    return render_template(
        "collection.html",
        category=category,
        documents=documents,
        fields=category_fields
    )

# -----------------------------
# 5. FORM ROUTE (ADD NEW)
# -----------------------------
@app.route("/form/<category>", methods=["GET", "POST"])
def add_form(category):
    """
    GET: Show a form to add a new doc to this category.
    POST: Insert new doc, then redirect to success.
    """
    if category not in collections_map:
        return "Invalid category!", 404

    col_name = collections_map[category]
    col = db[col_name]

    if request.method == "POST":
        # Build the doc from the form data
        new_doc = {}
        for field in fields_map[category]:
            new_doc[field] = request.form.get(field, "")

        # Prevent Duplicate Personnel
        if category == "personnel":
            existing = col.find_one({
                "name": new_doc["name"],
                "rank": new_doc["rank"]
            })
            if existing:
                flash("Duplicate personnel entry. Insert aborted!", "error")
                return redirect(url_for("home"))

        col.insert_one(new_doc)
        flash("Document inserted successfully!", "success")
        return redirect(url_for("success"))

    category_fields = fields_map[category]
    return render_template("form.html", category=category, fields=category_fields)

# -----------------------------
# 6. UPDATE ROUTE (LIKE ADD PAGE)
# -----------------------------
@app.route("/update/<category>/<doc_id>", methods=["GET", "POST"])
def update_doc(category, doc_id):
    """
    GET: Show a form (like 'Add Document') with existing values prefilled.
    POST: Update the document with new values under the same _id.
    """
    if category not in collections_map:
        return "Invalid category!", 404

    col_name = collections_map[category]
    col = db[col_name]

    existing_doc = col.find_one({"_id": ObjectId(doc_id)})
    if not existing_doc:
        flash("Document not found!", "error")
        return redirect(url_for("show_collection", category=category))

    if request.method == "POST":
        update_data = {}
        for field in fields_map[category]:
            new_val = request.form.get(field)
            if new_val is not None:
                update_data[field] = new_val

        # Auto-add completion_date if Missions is updated to 'Completed'
        if category == "missions" and update_data.get("status", "").lower() == "completed":
            update_data["completion_date"] = datetime.now().isoformat()

        col.update_one({"_id": ObjectId(doc_id)}, {"$set": update_data})
        flash("Document updated successfully!", "success")
        return redirect(url_for("show_collection", category=category))

    category_fields = fields_map[category]
    return render_template(
        "update.html",
        category=category,
        doc_id=doc_id,
        existing_doc=existing_doc,
        fields=category_fields
    )

# -----------------------------
# 7. DELETE ROUTE
# -----------------------------
@app.route("/delete/<category>/<doc_id>")
def delete_doc(category, doc_id):
    """
    Delete a document by _id, then redirect to the collection.
    """
    if category not in collections_map:
        return "Invalid category!", 404

    col_name = collections_map[category]
    col = db[col_name]

    # Log Deleted Missions
    if category == "missions":
        doc = col.find_one({"_id": ObjectId(doc_id)})
        if doc:
            db["mission_audit_log"].insert_one({
                **doc,
                "deleted_at": datetime.now().isoformat()
            })

    col.delete_one({"_id": ObjectId(doc_id)})
    flash("Document deleted successfully!", "success")
    return redirect(url_for("show_collection", category=category))

# -----------------------------
# 8. SUCCESS PAGE
# -----------------------------
@app.route("/success")
def success():
    return render_template("success.html")

# -----------------------------
# 9. RUN FLASK
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
