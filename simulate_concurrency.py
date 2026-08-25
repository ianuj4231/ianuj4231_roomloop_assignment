import threading
import requests


URL = "http://127.0.0.1:8000/bookings"


# booking1 = {
#     "room_id": 1,
#     "user_id": "user-1",
#     "start_time": "2026-09-07T03:00:00",
#     "end_time": "2026-09-07T07:00:00",
# }

# booking2 = {
#     "room_id": 1,
#     "user_id": "user-2",
#     "start_time": "2026-09-07T02:00:00",
#     "end_time": "2026-09-07T03:00:00",
# }


booking1 = {
    "room_id": 1,
    "user_id": "user-1",
    "start_time": "2026-09-07T07:00:00",
    "end_time": "2026-09-07T08:00:00",
}

booking2 = {
    "room_id": 1,
    "user_id": "user-2",
    "start_time": "2026-09-07T07:15:00",
    "end_time": "2026-09-07T07:45:00",
}



def create_booking(booking):
    response = requests.post(URL, json=booking)

    print(
        booking["user_id"],
        response.status_code,
        response.json()
    )


thread1 = threading.Thread(
    target=create_booking,
    args=(booking1,)
)

thread2 = threading.Thread(
    target=create_booking,
    args=(booking2,)
)

thread1.start()
thread2.start()

thread1.join()
thread2.join()


# SELECT r.timezone
# FROM bookings b
# JOIN rooms r ON r.id = b.room_id
# WHERE b.recurring_group_id = ?
# LIMIT 1;