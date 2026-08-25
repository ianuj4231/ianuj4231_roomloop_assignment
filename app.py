from fastapi import FastAPI,HTTPException
from datetime import datetime, date, timedelta

from database import get_connection, initialize_database
from pydantic import BaseModel
import uuid
import sqlite3
from zoneinfo import ZoneInfo

app = FastAPI()

initialize_database()


class BookingCreate(BaseModel):
    room_id: int
    user_id: str
    start_time: str
    end_time: str

class RecurringBookingCreate(BaseModel):
    room_id: int
    user_id: str
    start_time: datetime
    end_time: datetime
    repeat_until: date


@app.get("/health")
def health():
    return {"status": "ok"}








@app.get("/rooms")
def get_rooms():
    connection = get_connection()

    rows = connection.execute("""
        SELECT id, name, capacity
        FROM rooms
        ORDER BY id
    """).fetchall()

    connection.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "capacity": row[2],
        }
        for row in rows
    ]




@app.post("/bookings")
def create_booking(booking: BookingCreate):
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")
        ## transaction starts... needed for locking... locking queries need to be wrappped in a txn so  writes happen in a sequence for concurrency control.
        # 1. Validate room
        room = connection.execute(
            """
            SELECT id
            FROM rooms
            WHERE id = ?
            """,
            (booking.room_id,),
        ).fetchone()

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Room not found",
            )

        # 2. Validate time
        if booking.start_time >= booking.end_time:
            raise HTTPException(
                status_code=400,
                detail="start_time must be before end_time",
            )

        # 3. Check conflict
        conflict = connection.execute(
            """
            SELECT id
            FROM bookings
            WHERE room_id = ?
              AND start_time < ?
              AND end_time > ?
            LIMIT 1
            """,
            (
                booking.room_id,
                booking.end_time,
                booking.start_time,
            ),
        ).fetchone()

        if conflict is not None:
            raise HTTPException(
                status_code=409,
                detail="Room is already booked for this time",
            )

        # 4. Insert
        cursor = connection.execute(
            """
            INSERT INTO bookings (
                room_id,
                user_id,
                start_time,
                end_time,
                recurring_group_id
            )
            VALUES (?, ?, ?, ?, NULL)
            """,
            (
                booking.room_id,
                booking.user_id,
                booking.start_time,
                booking.end_time,
            ),
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "room_id": booking.room_id,
            "user_id": booking.user_id,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "recurring_group_id": None,
        }

    except HTTPException:
        connection.rollback()
        raise

    except sqlite3.OperationalError:
        connection.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database is busy, please retry",
        )

    finally:
        connection.close()





# @app.delete("/bookings/{booking_id}")
# def delete_booking(booking_id: int):
#     connection = get_connection()

#     try:
#         cursor = connection.execute(
#             """
#             DELETE FROM bookings
#             WHERE id = ?
#             """,
#             (booking_id,),
#         )

#         if cursor.rowcount == 0:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Booking not found",
#             )

#         connection.commit()

#         return {
#             "message": "Booking cancelled",
#             "booking_id": booking_id,
#         }

#     except Exception:
#         connection.rollback()
#         raise

#     finally:
#         connection.close()




@app.post("/bookings/recurring")
def create_recurring_booking(booking: RecurringBookingCreate):

    # 1. Validate booking time
    if booking.start_time >= booking.end_time:
        raise HTTPException(
            status_code=400,
            detail="start_time must be before end_time",
        )

    # 2. Validate repeat-until date
    if booking.repeat_until < booking.start_time.date():
        raise HTTPException(
            status_code=400,
            detail="repeat_until must be on or after the start date",
        )

    # 3. Generate weekly occurrences
    occurrences = []

    current_start = booking.start_time

    duration = booking.end_time - booking.start_time

    while current_start.date() <= booking.repeat_until:

        current_end = current_start + duration

        occurrences.append(
            (
                current_start,
                current_end,
            )
        )

        current_start = current_start + timedelta(days=7)

    # Critical development logging
    print("Generated occurrences:")

    for start, end in occurrences:
        print(
            f"  {start.strftime('%Y-%m-%dT%H:%M:%S')}"
            f" -> "
            f"{end.strftime('%Y-%m-%dT%H:%M:%S')}"
        )

    # 4. Determine the overall time range
    earliest_start = occurrences[0][0]
    latest_end = occurrences[-1][1]

    print("Overall recurrence window:")
    print(
        f"  {earliest_start.strftime('%Y-%m-%dT%H:%M:%S')}"
        f" -> "
        f"{latest_end.strftime('%Y-%m-%dT%H:%M:%S')}"
    )

    connection = get_connection()

    try:
        # 5. Start transaction
        connection.execute("BEGIN IMMEDIATE")

        print("Transaction started")

        # 6. Check that the room exists
        room = connection.execute(
            """
            SELECT id
            FROM rooms
            WHERE id = ?
            """,
            (booking.room_id,),
        ).fetchone()

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Room not found",
            )

        # 7. Fetch existing bookings that could overlap
        existing_bookings = connection.execute(
            """
            SELECT id, start_time, end_time
            FROM bookings
            WHERE room_id = ?
              AND start_time < ?
              AND end_time > ?
            ORDER BY start_time
            """,
            (
                booking.room_id,
                latest_end.strftime("%Y-%m-%dT%H:%M:%S"),
                earliest_start.strftime("%Y-%m-%dT%H:%M:%S"),
            ),
        ).fetchall()

        print("Existing candidate bookings:")

        for row in existing_bookings:
            print(
                f"  id={row[0]}"
                f"  {row[1]}"
                f" -> {row[2]}"
            )

        print(
            f"Found {len(existing_bookings)} candidate booking(s)"
        )



        # 8. Separate occurrences into conflicts and available
        available_occurrences = []
        conflicting_occurrences = []

        for occurrence_start, occurrence_end in occurrences:

            conflict = False

            for row in existing_bookings:

                existing_start = datetime.fromisoformat(row[1])
                existing_end = datetime.fromisoformat(row[2])

                # Two bookings overlap if:
                # existing starts before occurrence ends
                # AND existing ends after occurrence starts
                if (
                    existing_start < occurrence_end
                    and existing_end > occurrence_start
                ):
                    conflict = True
                    break

            if conflict:
                conflicting_occurrences.append(
                    (occurrence_start, occurrence_end)
                )
            else:
                available_occurrences.append(
                    (occurrence_start, occurrence_end)
                )

        print("Conflicting occurrences:")

        for start, end in conflicting_occurrences:
            print(
                f"  {start.strftime('%Y-%m-%dT%H:%M:%S')}"
                f" -> "
                f"{end.strftime('%Y-%m-%dT%H:%M:%S')}"
            )

        print("Available occurrences:")

        for start, end in available_occurrences:
            print(
                f"  {start.strftime('%Y-%m-%dT%H:%M:%S')}"
                f" -> "
                f"{end.strftime('%Y-%m-%dT%H:%M:%S')}"
            )

        print(
            f"Conflicts: {len(conflicting_occurrences)}"
        )

        print(
            f"Available: {len(available_occurrences)}"
        )


        # 9. Create one group ID for the entire recurring series
        recurring_group_id = str(uuid.uuid4())

        print(
            f"Recurring group ID: {recurring_group_id}"
        )




        # 10. Insert all available occurrences
        rows_to_insert = [
            (
                booking.room_id,
                booking.user_id,
                start.strftime("%Y-%m-%dT%H:%M:%S"),
                end.strftime("%Y-%m-%dT%H:%M:%S"),
                recurring_group_id,
            )
            for start, end in available_occurrences
        ]
        ## https://docs.python.org/uk/3.14/library/sqlite3.html?utm_source=chatgpt.com#sqlite3.Cursor.executemany
        
        connection.executemany(
            """
            INSERT INTO bookings (
                room_id,
                user_id,
                start_time,
                end_time,
                recurring_group_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )

        print(
            f"Inserted {len(rows_to_insert)} booking(s)"
        )







        # 11. Commit the entire recurring booking
        connection.commit()

        print("Transaction committed")

        return {
            "message": "Recurring booking created",
            "recurring_group_id": recurring_group_id,
            "created_count": len(rows_to_insert),
            "conflict_count": len(conflicting_occurrences),
        }







    except HTTPException:
        connection.rollback()
        raise

    except sqlite3.OperationalError:
        connection.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database is busy, please retry",
        )

    finally:
        connection.close()









@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int):

    connection = get_connection()

    try:
        print(f"DELETE request received for booking_id={booking_id}")

        # 1. Find the booking and room timezone
        booking = connection.execute(
            """
            SELECT
                b.id,
                b.room_id,
                b.recurring_group_id,
                r.timezone
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            WHERE b.id = ?
            """,
            (booking_id,),
        ).fetchone()

        print(f"Booking found: {booking}")

        if booking is None:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        booking_id_from_db = booking[0]
        room_id = booking[1]
        recurring_group_id = booking[2]
        room_timezone = booking[3]

        print(f"Room ID: {room_id}")
        print(f"Recurring group ID: {recurring_group_id}")
        print(f"Room timezone: {room_timezone}")

        # 2. Normal single booking
        if recurring_group_id is None:

            print(
                f"Deleting single booking id={booking_id}"
            )

            cursor = connection.execute(
                """
                DELETE FROM bookings
                WHERE id = ?
                """,
                (booking_id,),
            )

            print(
                f"DELETE affected {cursor.rowcount} row(s)"
            )

            connection.commit()

            print("Single booking DELETE committed")

            # Verify deletion
            remaining = connection.execute(
                """
                SELECT id
                FROM bookings
                WHERE id = ?
                """,
                (booking_id,),
            ).fetchone()

            print(
                f"Booking after DELETE: {remaining}"
            )

            return {
                "message": "Booking cancelled",
                "booking_id": booking_id,
            }

        # 3. Recurring booking
        print(
            f"Recurring group: {recurring_group_id}"
        )

        # 4. Determine current time in room timezone
        now = datetime.now(
            ZoneInfo(room_timezone)
        )

        # Stored timestamps are naive local ISO strings
        now_local = now.replace(
            tzinfo=None
        )

        now_string = now_local.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )

        print(
            f"Cancellation time: {now_string}"
        )

        # 5. Delete only future instances
        cursor = connection.execute(
            """
            DELETE FROM bookings
            WHERE recurring_group_id = ?
              AND start_time >= ?
            """,
            (
                recurring_group_id,
                now_string,
            ),
        )

        deleted_count = cursor.rowcount

        print(
            f"Deleted {deleted_count} future occurrence(s)"
        )

        connection.commit()

        print("Recurring DELETE committed")

        return {
            "message": "Recurring booking cancelled",
            "booking_id": booking_id,
            "recurring_group_id": recurring_group_id,
            "deleted_count": deleted_count,
        }

    except HTTPException:
        raise

    except sqlite3.OperationalError:
        raise HTTPException(
            status_code=503,
            detail="Database is busy, please retry",
        )

    finally:
        connection.close()