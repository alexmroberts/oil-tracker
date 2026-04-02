async function getStatus() {
    try {
        const response = await fetch('/oiltracker/api/prices?limit=1');
        const json = await response.json();
        if (json.data.length > 0) {
            const lastDate = new Date(json.data[0].scraped_at).toLocaleString();
            document.getElementById('status-text').innerText = `Last update: ${lastDate}`;
        }
    } catch (e) {
        console.log("Oil Tracker API not reachable");
    }
}

getStatus();