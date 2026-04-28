from langchain.tools import tool
from app.storage.test_db import dbb, Users, Experience, Education, Projects, Activites_and_Interests, References



# ── FETCH — get all rows for a user from a table ──────────────
def get_data(email, name_of_table):

    user_found = Users.query.filter_by(email=email).first()

    if not user_found:
        return False, "User not found"

    rows = name_of_table.query.filter_by(user_id=user_found.id).all()

    if not rows:
        return False, "No data found"

    # Return as a list of dicts so the AI can read it easily
    result = []
    for row in rows:
        result.append({
            "row_id": row.__mapper__.primary_key_from_instance(row)[0],
            "detail": row.detail
        })

    return True, result


# ── ADD — insert a new row ─────────────────────────────────────
def add_data(email, name_of_table, new_detail):

    user_found = Users.query.filter_by(email=email).first()

    if not user_found:
        return False, "User not found"

    new_row = name_of_table(user_id=user_found.id, detail=new_detail)
    dbb.session.add(new_row)
    dbb.session.commit()

    return True, "Added successfully"


# ── UPDATE — update a specific row ────────────────────────────

def update_data(email, name_of_table, row_id, new_detail):

    user_found = Users.query.filter_by(email=email).first()

    if not user_found:
        return False, "User not found"

    row = dbb.session.get(name_of_table, row_id)

    if not row:
        return False, "Row not found"

    if row.user_id != user_found.id:
        return False, "Permission denied"

    row.detail = new_detail
    dbb.session.commit()

    return True, "Updated successfully"


# ── DELETE — remove a specific row ────────────────────────────
def delete_data(email, name_of_table, row_id):

    user_found = Users.query.filter_by(email=email).first()

    if not user_found:
        return False, "User not found"

    row = dbb.session.get(name_of_table, row_id)

    if not row:
        return False, "Row not found"

    if row.user_id != user_found.id:
        return False, "Permission denied"

    dbb.session.delete(row)
    dbb.session.commit()

    return True, "Deleted successfully"
# ```

# ---

# ## How the AI uses these together

# When connected to the LLM, the conversation will work like this:
# ```
# User:  "Update my Amazon experience to include team leadership"
#          ↓
# AI calls get_data(email, Experience)
#          ↓
# Gets back:
#   [
#     {"row_id": 1, "detail": "Worked at Google 2020-2023"},
#     {"row_id": 2, "detail": "Worked at Amazon 2018-2020"}
#   ]
#          ↓
# AI identifies row_id=2 is the Amazon one
#          ↓
# AI calls update_data(email, Experience, row_id=2, new_detail="Worked at Amazon 2018-2020, led a team of 5")
#          ↓
# Database updated