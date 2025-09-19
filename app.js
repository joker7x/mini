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
  video.onerror = null;

  // أضف زر فتح خارجيًا دائماً
  let openBtn = document.getElementById('open-external-btn');
  if (openBtn) openBtn.remove();
  openBtn = createButton('فتح الرابط خارجيًا', () => window.open(url, '_blank'));
  openBtn.id = 'open-external-btn';
  document.getElementById('qualities').appendChild(openBtn);

  // التعامل مع m3u8
  if (/\.m3u8(\b|$)/i.test(url)) {
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = url;
      video.play();
    } else if (window.Hls && Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, function () {
        video.play();
      });
      hls.on(Hls.Events.ERROR, function () {
        setStatus('تعذر تشغيل فيديو m3u8، حاول فتح الرابط خارجيًا.');
      });
    } else {
      setStatus('متصفحك لا يدعم m3u8 مباشرة أو عبر Hls.js.');
    }
    return;
  }

  // الأنواع الشائعة
  if (
    /\.mp4(\b|$)/i.test(url) ||
    /\.webm(\b|$)/i.test(url) ||
    /\.ogg(\b|$)/i.test(url)
  ) {
    video.src = url;
    video.play();
    video.onerror = function () {
      setStatus('تعذر تشغيل الفيديو، حاول فتح الرابط خارجيًا.');
    };
    return;
  }

  // أي نوع آخر: جرب تشغيله مباشرة
  video.src = url;
  video.play();
  video.onerror = function () {
    setStatus('نوع الفيديو غير مدعوم أو تعذر تشغيله، حاول فتح الرابط خارجيًا.');
  };
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
