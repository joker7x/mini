// استقبال بيانات الحلقات والجودات تلقائيًا من Telegram WebApp
let data = [];
function getEpisodesFromTelegram() {
  try {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
      // استخرج البيانات من initData (مثال: episodes=JSON)
      const params = new URLSearchParams(window.Telegram.WebApp.initData);
      if (params.get('episodes')) {
        data = JSON.parse(params.get('episodes'));
      }
    }
  } catch(e) { /* fallback */ }
}
// استدعاء الدالة عند التحميل
getEpisodesFromTelegram();

// بيانات تجريبية لو لم تصل بيانات من البوت
if (!data || !Array.isArray(data) || data.length === 0) {
  data = [
    {
      title: "آل سوبرانو - الحلقة 1",
      sources: [
        { label: "1080p", url: "https://server-hls2-stream-c31.cdn-tube.xyz/v/02/00057/d1c49e018tmo_x/x.mp4?t=MFy6ahoW75J9iPuJ4P29Dizc0guq41gCRM0pEnlI4WM&s=1758283159&e=86400&f=288404&sp=30000&i=0.0" },
        { label: "720p", url: "https://server-hls2-stream-c31.cdn-tube.xyz/v/02/00057/d1c49e018tmo_h/h.mp4?t=THwnCJEmLpU5efCo4caRRLIWky5sTrC5TbfGHtU4Fmw&s=1758283159&e=86400&f=288404&sp=30000&i=0.0" },
        { label: "480p", url: "https://server-hls2-stream-c31.cdn-tube.xyz/v/02/00057/d1c49e018tmo_n/n.mp4?t=vXNzLM5chKCaTLHtFx5ddKywOcQzRTJi8Uu2Rtud_J4&s=1758283159&e=86400&f=288404&sp=30000&i=0.0" },
        { label: "240p Mobile", url: "https://server-hls2-stream-c31.cdn-tube.xyz/v/02/00057/d1c49e018tmo_l/l.mp4?t=dQ68tV40BZdlh9yU5UZNqJlS4d1ssWT_c-k7LmnXCqA&s=1758283159&e=86400&f=288404&sp=30000&i=0.0" }
      ]
    }
    // أضف المزيد من الحلقات بنفس الطريقة لو أردت
  ];
}

// عناصر الصفحة
const episodesList = document.getElementById('episodes-list');
const playerArea = document.getElementById('player-area');
const episodeTitle = document.getElementById('episode-title');
const qualityButtons = document.getElementById('quality-buttons');
const video = document.getElementById('video');
const status = document.getElementById('status');
const backBtn = document.getElementById('back-btn');
const externalLink = document.getElementById('external-link');
const openExternalBtn = document.getElementById('open-external-btn');

let currentEpisode = null;
let currentSource = null;
let hls = null;

// عرض الحلقات
function showEpisodes() {
  episodesList.innerHTML = '';
  playerArea.style.display = 'none';
  document.getElementById('episodes-area').style.display = 'block';
  data.forEach((ep, idx) => {
    const btn = document.createElement('button');
    btn.className = 'episode-btn';
    btn.textContent = ep.title;
    btn.onclick = () => selectEpisode(idx);
    episodesList.appendChild(btn);
  });
}
showEpisodes();

function selectEpisode(idx) {
  currentEpisode = data[idx];
  episodeTitle.textContent = currentEpisode.title;
  document.getElementById('episodes-area').style.display = 'none';
  playerArea.style.display = 'block';
  showQualities(currentEpisode.sources);
  video.src = '';
  status.textContent = 'اختر الجودة أولاً.';
  externalLink.style.display = 'none';
}

function showQualities(sources) {
  qualityButtons.innerHTML = '';
  sources.forEach((src, i) => {
    const btn = document.createElement('button');
    btn.className = 'quality-btn';
    btn.textContent = src.label;
    btn.onclick = () => playSource(src);
    qualityButtons.appendChild(btn);
  });
}

// تشغيل المصدر المختار
function playSource(src) {
  currentSource = src;
  status.textContent = '';
  externalLink.style.display = 'none';
  // تنظيف HLS القديم
  if (hls) {
    hls.destroy();
    hls = null;
  }
  video.poster = "cinema-poster.png";
  video.src = "";
  // دعم m3u8
  if (src.url.endsWith('.m3u8')) {
    if (Hls.isSupported()) {
      hls = new Hls();
      hls.loadSource(src.url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, function () {
        video.play();
        status.textContent = '';
      });
      hls.on(Hls.Events.ERROR, function (event, data) {
        status.textContent = '⚠️ لم يتم تشغيل الفيديو! قد يكون الرابط محمي أو يحتاج فتح خارجي.';
        externalLink.style.display = 'block';
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src.url;
      video.addEventListener('loadedmetadata', () => video.play());
    } else {
      status.textContent = '⚠️ متصفحك لا يدعم تشغيل هذا النوع. افتح الرابط خارجيًا.';
      externalLink.style.display = 'block';
    }
  } else {
    // أنواع الفيديو الأخرى
    video.src = src.url;
    video.load();
    video.play().catch(() => {
      status.textContent = '⚠️ لم يتم تشغيل الفيديو! افتح الرابط خارجيًا.';
      externalLink.style.display = 'block';
    });
    video.onerror = () => {
      status.textContent = '⚠️ لم يتم تشغيل الفيديو! افتح الرابط خارجيًا.';
      externalLink.style.display = 'block';
    };
  }
}

openExternalBtn.onclick = function() {
  if (currentSource) window.open(currentSource.url, "_blank");
};

backBtn.onclick = function() {
  showEpisodes();
};
