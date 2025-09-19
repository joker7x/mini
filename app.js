function parseQuery() {
  const p = new URLSearchParams(location.search);
  const s = p.get('s');
  if (!s) return null;
  try {
    const json = atob(s.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch (e) {
    return null;
  }
}

function createButton(label, onClick) {
  const b = document.createElement('button');
  b.textContent = label;
  b.className = 'qbtn';
  b.addEventListener('click', onClick);
  return b;
}

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}

function play(url) {
  const video = document.getElementById('video');
  if (Hls.isSupported() && /\.m3u8(\b|$)/i.test(url)) {
    const hls = new Hls();
    hls.loadSource(url);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, function () {
      video.play();
    });
  } else {
    video.src = url;
    video.play();
  }
}

function init() {
  const data = parseQuery();
  if (!data || !Array.isArray(data.sources) || data.sources.length === 0) {
    setStatus('لا يوجد مصادر.');
    return;
  }
  setStatus('اختر الجودة:');
  const holder = document.getElementById('qualities');
  holder.innerHTML = '';
  data.sources.forEach((s) => {
    const label = s.q || 'Auto';
    const url = s.u;
    const btn = createButton(label, () => play(url));
    holder.appendChild(btn);
  });
}

document.addEventListener('DOMContentLoaded', init);


