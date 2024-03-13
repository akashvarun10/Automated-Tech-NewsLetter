let selectedChannels = [];

function searchChannels() {
    const searchInput = document.getElementById('searchInput').value;
    const resultsDiv = document.getElementById('results');
    const warningDiv = document.getElementById('warning');
    resultsDiv.innerHTML = '';
    warningDiv.textContent = '';

    const apiKey = 'yourapikeyhere';
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

function sendEmail() {
const emailInput = document.getElementById('email').value;
const warningDiv = document.getElementById('warning');

if (selectedChannels.length === 0) {
    warningDiv.textContent = 'Please select at least one channel.';
    return;
}

fetch('/send-email', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ selectedChannels, recipientEmail: emailInput })
})
.then(response => {
    if (response.ok) {
        console.log('Email sent successfully');
        warningDiv.textContent = '';
    } else {
        console.error('Failed to send email');
        warningDiv.textContent = 'Failed to send email';
    }
})
.catch(error => {
    console.error('Error sending data to server:', error);
    warningDiv.textContent = 'Failed to send email';
});
}