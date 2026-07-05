const { Innertube } = require('youtubei.js');
const fs = require('fs');

async function updateLinks() {
  const channels = JSON.parse(fs.readFileSync('channels.json', 'utf8'));
  const yt = await Innertube.create();
  let results = {};

  for (const [name, id] of Object.entries(channels)) {
    try {
      const info = await yt.getInfo(id);
      results[name] = info.streaming_data?.hls_manifest_url || "OFFLINE";
    } catch (e) {
      results[name] = "ERROR";
    }
  }
  // Simpen hasil akhirnya ke file buat dibaca web lu
  fs.writeFileSync('stream_links.json', JSON.stringify(results, null, 2));
}

updateLinks();
