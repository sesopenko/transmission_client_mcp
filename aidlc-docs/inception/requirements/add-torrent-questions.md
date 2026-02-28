# add_torrent Behaviour Questions

Please answer the following questions about the `add_torrent` tool behaviour.
Fill in the letter choice after each `[Answer]:` tag. Let me know when you're done.

---

## Question 1
What input types should `add_torrent` accept?

A) Magnet links only
B) Magnet links and HTTP/HTTPS URLs (Transmission fetches the .torrent file)
C) Magnet links, HTTP/HTTPS URLs, and local .torrent file paths
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 2
Should the caller be able to specify a download directory (where files are saved)?

A) No — always use Transmission's default download directory
B) Yes — optional parameter to override the download directory for this torrent
X) Other (please describe after [Answer]: tag below)

[Answer]: X

Yes — optional parameter to override the download directory for this torrent

With a potential added feature:  if the transmission-rpc library supports fetching the default download folder for the
remote transmission host then reject downloads outside that folder.

Example:

transmission is configured as `/downloads` as the default download directory

Allowed:

`/downloads/somewhere/that/is/allowed`
`/downloads`

Not allowed
`/tmp/somewhere/else`
`/var/somewhere/else`
---

## Question 3
Should the torrent start downloading immediately after being added?

A) Yes — always start immediately
B) No — always add in stopped/paused state
C) Use Transmission's default behaviour (respects the "start when added" setting)
D) Optional parameter — caller can specify start or paused; default to Transmission's setting
X) Other (please describe after [Answer]: tag below)

[Answer]: X

C, if the transmission-rpc library supports it.  Otherwise, A.

---

## Question 4
What should `add_torrent` return on success?

A) A simple confirmation message: "Torrent added successfully"
B) Confirmation message plus the torrent name (as Transmission resolved it)
C) Confirmation message plus name, status, and size
X) Other (please describe after [Answer]: tag below)

[Answer]: X

For .torrent files, C
For magnet links: A, because magnet links will take a while to get details on the torrent.

---

## Question 5
What should happen if the same torrent is added twice (duplicate)?

A) Return an error message indicating the torrent already exists
B) Silently succeed — let Transmission handle it (it will reject the duplicate internally)
C) Return a clear message distinguishing "already exists" from a true error
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 6
Should there be any validation of the input before sending it to Transmission?

A) No validation — pass the input directly to Transmission and let it error if invalid
B) Basic format validation — check that the input looks like a magnet link, URL, or file path before sending
X) Other (please describe after [Answer]: tag below)

[Answer]: X

Basic format validation — check that the input looks like a magnet link, URL

(file paths not supported)
