# get_torrent Behaviour Questions

Please answer the following questions about the `get_torrent` tool behaviour.
Fill in the letter choice after each `[Answer]:` tag. Let me know when you're done.

---

## Question 1
How should the torrent be identified when calling `get_torrent`?

A) By Transmission's internal numeric ID
B) By torrent name (exact match)
C) By torrent name (case-insensitive substring match — errors if more than one match)
D) By either numeric ID or name (caller chooses)
X) Other (please describe after [Answer]: tag below)

[Answer]: X

Work through solving which method will work best with an LLM and then provide justification as a short description.

---

## Question 2
What information should `get_torrent` return?

A) Everything from `list_torrents` for that single torrent (no additional fields)
B) Everything from `list_torrents` plus: save path, date added, ratio, tracker list
C) Everything from `list_torrents` plus: save path, date added, ratio, tracker list, file list (name + size + progress per file), peer list
X) Other (please describe after [Answer]: tag below)

[Answer]: X

Everything from `list_torrents` plus: save path, date added, ratio, file list (name + size + progress per file), Error message if in error state.

example error message "Blacklisted client, update or change client"

---

## Question 3
What should happen if no torrent is found matching the identifier?

A) Return an error message: "No torrent found matching '[identifier]'"
B) Return an empty result with no message
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
If matching by name and multiple torrents match, what should happen?

A) Return an error listing the matching names so the caller can refine their query
B) Return all matching torrents
C) N/A — I chose exact match or ID-only in Question 1
X) Other (please describe after [Answer]: tag below)

[Answer]: X

Work through what will be the easiest for an LLM to work with and provide a justification.
