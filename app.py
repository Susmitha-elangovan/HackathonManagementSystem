from flask import Flask, render_template, request, redirect, url_for
from database import get_db_connection

app = Flask(__name__)


# =========================
# EVENTS PAGE
# =========================
@app.route("/")
@app.route("/events")
def events():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            e.event_id,
            e.event_name,
            e.event_date,
            e.venue,
            e.capacity,
            o.name AS organizer,
            COUNT(r.registration_id) AS registered
        FROM Event e
        LEFT JOIN Organizer o
            ON e.organizer_id = o.organizer_id
        LEFT JOIN Registration r
            ON e.event_id = r.event_id
        GROUP BY
            e.event_id,
            e.event_name,
            e.event_date,
            e.venue,
            e.capacity,
            o.name
        ORDER BY e.event_date
    """

    cursor.execute(query)

    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("events.html", events=events)


# =========================
# ADD EVENT
# =========================
@app.route("/add_event", methods=["GET", "POST"])
def add_event():

    if request.method == "POST":

        event_name = request.form["event_name"]
        event_date = request.form["event_date"]
        venue = request.form["venue"]
        capacity = request.form["capacity"]
        organizer_id = request.form["organizer_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO Event
            (event_name, event_date, venue, capacity, organizer_id)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                event_name,
                event_date,
                venue,
                capacity,
                organizer_id
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("events"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Organizer")

    organizers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_event.html",
        organizers=organizers
    )


# =========================
# EDIT EVENT
# =========================
@app.route("/edit_event/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        event_name = request.form["event_name"]
        event_date = request.form["event_date"]
        venue = request.form["venue"]
        capacity = request.form["capacity"]
        organizer_id = request.form["organizer_id"]

        query = """
            UPDATE Event
            SET
                event_name = %s,
                event_date = %s,
                venue = %s,
                capacity = %s,
                organizer_id = %s
            WHERE event_id = %s
        """

        cursor.execute(
            query,
            (
                event_name,
                event_date,
                venue,
                capacity,
                organizer_id,
                event_id
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("events"))

    cursor.execute(
        "SELECT * FROM Event WHERE event_id = %s",
        (event_id,)
    )

    event = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM Organizer"
    )

    organizers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "edit_event.html",
        event=event,
        organizers=organizers
    )


# =========================
# DELETE EVENT
# =========================
@app.route("/delete_event/<int:event_id>")
def delete_event(event_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM Registration WHERE event_id = %s",
        (event_id,)
    )

    cursor.execute(
        "DELETE FROM Event WHERE event_id = %s",
        (event_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("events"))


# =========================
# REGISTER
# =========================
@app.route("/register/<int:event_id>", methods=["GET", "POST"])
def register(event_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Event WHERE event_id = %s",
        (event_id,)
    )

    event = cursor.fetchone()

    if request.method == "POST":

        student_id = request.form["student_id"]

        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM Registration
            WHERE event_id = %s
            """,
            (event_id,)
        )

        result = cursor.fetchone()

        if result["count"] >= event["capacity"]:

            cursor.close()
            conn.close()

            return """
            <h2>Registration Failed</h2>
            <p>This event is already full.</p>
            <a href="/events">Back to Events</a>
            """

        cursor.execute(
            """
            SELECT *
            FROM Registration
            WHERE student_id = %s
            AND event_id = %s
            """,
            (student_id, event_id)
        )

        existing = cursor.fetchone()

        if existing:

            cursor.close()
            conn.close()

            return """
            <h2>Already Registered</h2>
            <p>You have already registered for this event.</p>
            <a href="/events">Back to Events</a>
            """

        cursor.execute(
            """
            INSERT INTO Registration
            (
                student_id,
                event_id,
                registration_date,
                status
            )
            VALUES
            (
                %s,
                %s,
                CURDATE(),
                'Registered'
            )
            """,
            (student_id, event_id)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return render_template(
            "success.html",
            event=event
        )

    cursor.close()
    conn.close()

    return render_template(
        "register.html",
        event=event
    )


# =========================
# START APPLICATION
# =========================
if __name__ == "__main__":
    app.run(debug=True)