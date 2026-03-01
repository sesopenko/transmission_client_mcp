In **Transmission**, the **Seeds** and **Peers** columns show your torrent’s connection status within the swarm.

The format is:

> Connected / Total Known


---

## 🌱 Seeds (e.g., `38 / 3,162`)

- **First number (38)** → How many seeders you are *currently connected to*.
- **Second number (3,162)** → Total number of seeders known in the swarm (from trackers/DHT/PEX).

**Seeders** are users who have **100% of the file** and are uploading it.

So in this example:
- You are connected to **38 seeders**
- There are **3,162 seeders available** in total

---

## 👥 Peers (e.g., `0 / 51`)

- **First number (0)** → How many peers you are currently connected to.
- **Second number (51)** → Total known peers in the swarm.

**Peers** are users who are still downloading (they don’t have 100% yet).

So in this example:
- You are connected to **0 peers**
- There are **51 peers available**

---

## Why this matters

- More **seeds** = usually faster downloads.
- More connected peers/seeds = better speeds (up to your connection limits).
- If the first number is low, you may be limited by:
  - Your max peer connection settings
  - Network/firewall issues
  - The torrent’s health