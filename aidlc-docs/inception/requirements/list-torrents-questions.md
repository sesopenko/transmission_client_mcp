# list_torrents Behaviour Questions

Please answer the following questions about the `list_torrents` tool behaviour.
Fill in the letter choice after each `[Answer]:` tag. Let me know when you're done.

---

## Question 1
What information should be returned for each torrent?

A) Minimal: name, status (stopped/downloading/seeding), and progress percentage
B) Standard: name, status, progress %, download speed, upload speed, size, ETA
C) Detailed: everything in B plus ratio, peer count, save path, date added, tracker
X) Other (please describe after [Answer]: tag below)

[Answer]:X

* added on (ISO 8601 string; null if unavailable)
* name
* size (human-readable, variable units e.g. "4.2 GB")
* percentage done (e.g. "73.5%")
* status
* seeds — connected seeders / total known seeders (e.g. "4/12"). Connected seeders are peers with 100% download progress; total is the max seeder count from tracker stats. Matches the Seeds column in the Transmission desktop client.
* peers — connected leechers / total known leechers (e.g. "2/8"). Connected leechers are peers with less than 100% download progress; total is the max leecher count from tracker stats. Matches the Peers column in the Transmission desktop client.
* download speed (human-readable, variable units e.g. "3.2 MB/s", "512 KB/s")
* upload speed (human-readable, variable units e.g. "1.1 MB/s", "256 KB/s")
* ETA (HH:MM:SS, or "N/A" when not applicable)

---

## Question 2
Should `list_torrents` support filtering by status?

A) No filtering — always return all torrents
B) Optional status filter — caller can pass a status (e.g. "downloading", "seeding", "stopped") to narrow results
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
Should `list_torrents` support searching/filtering by name?

A) No — always return all torrents (or all matching the status filter)
B) Yes — optional name search parameter (substring match, case-insensitive)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
How should the list be sorted?

A) No guaranteed order (whatever Transmission returns)
B) Always sorted alphabetically by name
C) Sorted by date added (newest first)
D) Sorted by status then by name
X) Other (please describe after [Answer]: tag below)

[Answer]: X

Date added (oldest first), for a "first in first out" process that I tend to follow when working with files.

---

## Question 5
What should happen when there are no torrents (or no torrents match the filter)?

A) Return an empty list with a message like "No torrents found"
B) Return an empty list with no message
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6
Should there be a limit on how many torrents are returned at once?

A) No limit — always return all matching torrents
B) Yes — a configurable max (default 50), with a note if results were truncated
X) Other (please describe after [Answer]: tag below)

[Answer]: A
