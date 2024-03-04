const axios = require('axios');
const cheerio = require('cheerio');
const nodemailer = require('nodemailer');

// Function to check for new videos on the YouTube channel
async function checkNewVideos(channelUrl) {
  const response = await axios.get(channelUrl);
  const $ = cheerio.load(response.data);

  const videos = [];
  $('.style-scope ytd-grid-video-renderer').each((index, element) => {
    const videoTitle = $(element).find('#video-title').text().trim();
    const videoUrl = 'https://www.youtube.com' + $(element).find('#thumbnail').parent().attr('href');
    videos.push({ title: videoTitle, url: videoUrl });
  });

  return videos;
}

// Function to send an email notification
async function sendEmail(videoTitle, videoUrl, recipientEmail) {
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: 'your@gmail.com', // Replace with your Gmail email address
      pass: 'your_password', // Replace with your Gmail password or an app-specific password
    },
  });

  const mailOptions = {
    from: 'your@gmail.com', // Replace with your Gmail email address
    to: recipientEmail,
    subject: 'New Video Uploaded',
    text: `New video uploaded: ${videoTitle}\nWatch it here: ${videoUrl}`,
  };

  await transporter.sendMail(mailOptions);
}

// Main function to continuously check for new videos and send email notification
async function main() {
  const CHANNEL_URL = 'YOUR_CHANNEL_URL'; // Replace with your actual channel URL
  const RECIPIENT_EMAIL = 'recipient@example.com'; // Replace with the recipient's email address

  while (true) {
    const videos = await checkNewVideos(CHANNEL_URL);

    if (videos.length > 0) {
      const latestVideo = videos[0];
      await sendEmail(latestVideo.title, latestVideo.url, RECIPIENT_EMAIL);
    }

    // Adjust the interval based on your requirements (e.g., check every 1 hour)
    await new Promise(resolve => setTimeout(resolve, 3600000));
  }
}

main().catch(console.error);
