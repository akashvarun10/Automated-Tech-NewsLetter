let selectedChannels = [];

function searchChannels() {
    const searchInput = document.getElementById('searchInput').value;
    const resultsDiv = document.getElementById('results');
    const warningDiv = document.getElementById('warning');
    resultsDiv.innerHTML = '';
    warningDiv.innerHTML = '';

    // You can replace 'YOUR_API_KEY' with your actual YouTube Data API key
    const apiKey = 'AIzaSyA9hyG8URGR5Bi63a5AgDdv4Z34SJsyiCc';

    fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&q=${searchInput}&type=channel&key=${apiKey}`)
        .then(response => response.json())
        .then(data => {
            const channels = data.items;
            channels.forEach(channel => {
                const channelTitle = channel.snippet.title;
                const channelId = channel.id.channelId;
                const channelImage = channel.snippet.thumbnails.default.url;

                const channelDiv = document.createElement('div');
                channelDiv.className = 'channel-card';
                channelDiv.innerHTML = `
                    <img src="${channelImage}" alt="${channelTitle}">
                    <strong>${channelTitle}</strong><br>
                    Channel ID: ${channelId}<br>
                    <button onclick="selectChannel('${channelId}', '${channelTitle}', '${channelImage}')">Select</button>
                `;
                resultsDiv.appendChild(channelDiv);
            });
        })
        .catch(error => console.error('Error fetching data:', error));
}

function selectChannel(channelId, channelTitle, channelImage) {
    const warningDiv = document.getElementById('warning');
    if (!selectedChannels.some(channel => channel.id === channelId)) {
        selectedChannels.push({ id: channelId, title: channelTitle, image: channelImage });

        const selectedChannelsList = document.getElementById('selectedChannels');
        const listItem = document.createElement('li');
        listItem.innerHTML = `
            <img src="${channelImage}" alt="${channelTitle}">
            <strong>${channelTitle}</strong> (ID: ${channelId})<br>
        `;
        selectedChannelsList.appendChild(listItem);
    } else {
        warningDiv.textContent = 'This channel is already selected.';
    }
}
