# Decisions:


## decisions you made where this brief did not tell you what to do, and why;

**(a)**

* **Concurrency:** Used SQLite transaction/locking during booking creation so concurrent requests cannot both pass the availability check and create conflicting bookings.

* **Indexing:** Added indexes on `(room_id, start_time)` and `(recurring_group_id, start_time)` to speed up room availability checks and recurring-series cancellation, at the cost of a small write/storage overhead.

* **Recurring storage:** Stored each recurring occurrence as a separate booking row with a shared `recurring_group_id`, making future cancellation and occurrence-level queries straightforward.

* **Recurring cancellation:** Cancelling a recurring booking removes only future occurrences and preserves past occurrences.

* **Timezone:** Used the room's timezone when determining whether a recurring occurrence is in the future, rather than the server's timezone.


**//////////////////////////////////////////////////////////////////////////////////////////////////////////////**

## questions you would ask the PM before this ships

**(b)** 


Should rooms be bookable 24/7, or only during defined operating hours (e.g. daytime)? The current implementation allows bookings at any time; I would confirm the expected business hours before enforcing such a restriction.

////////////////////

Expected scale: The current requirement mentions around 200 users. Is this expected to grow significantly? If so, I would consider moving from SQLite to PostgreSQL/MySQL to support higher concurrent write throughput and more granular/row-level locking.coz SQLite serializes writes and slower at large scale. even if two people hit the server at the exact same microsecond,  postgres GiST index tree helps  for faster writes in a non-blocking way (i.e,people targetting different rooms will not be blocked by preceding writes). helps in range based overlaps.

intuition of postgres GiST working:

(i). Different Rooms = Different Branches (Parallel Tracks)
When Room 1 and Room 2 are processed, PostgreSQL uses the room_id to route them down completely separate branches of the index tree.

Because they live on separate branches, they run in parallel at the exact same microsecond without blocking each other.

(ii). Same Room = Same Branch (Sequentialized Safety)
When two requests come in for the same room (like your booking1 and booking2 for Room 1), they both go down the exact same branch of the tree.

Within that specific branch, things are serialized (ordered): The database engine processes one right after the other. The first one gets written, and the second one hits the GiST exclusion constraint, sees the time overlap, and gets cleanly blocked with a 409 Conflict.

reference link - https://www.youtube.com/watch?v=eG_9lZrrbEY

////////////////////

For recurring bookings, should cancellation remove all future occurrences or allow cancellation from a specific occurrence onward?


**//////////////////////////////////////////////////////////////////////////////////////////////////////////////**


## AI Assistance

**(c)**

* AI helped review the booking and concurrency logic and suggested indexing the booking lookup patterns. I validated this and added indexes on `(room_id, start_time)` and `(recurring_group_id, start_time)` to avoid unnecessary full-table scans as the data grows, indexing make reads faster but with a con of slower writes and higher cost to maintain indexes.

* The initial booking implementation did not adequately protect against two users concurrently booking overlapping times. I identified this race condition and added a `BEGIN IMMEDIATE` transaction to serialize the availability check and booking write.

* AI initially missed that `ZoneInfo` required the `tzdata` package in the Windows environment. I identified the error during testing and added the required dependency.

**//////////////////////////////////////////////////////////////////////////////////////////////////////////////**


**(c)**


## Deliberately Left Out

* **Authentication, authorization and admin roles:** Not implemented because the brief does not define authentication or admin requirements. Next, I would add user authentication, ownership checks, and separate admin permissions if required.

* **Cancellation history:** Bookings are currently deleted rather than soft-deleted. For production, I would retain cancellation/audit records.

 for evaluator wanted quick setup so proceeded with sqlite... for production postgres GiST can be used...coz its extendible to more no of people provides room-level lock and doesnt block people who want to book another room plus range based indexing is there using GiST.