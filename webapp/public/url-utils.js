(() => {
  function buildAuthorUrl(recordUrl, webMode, host, version) {
    try {
      const source = new URL(recordUrl);
      if (!['http:', 'https:'].includes(source.protocol)) return '';
      if (!webMode) {
        if (source.hostname === '192.168.10.26') source.hostname = 'localhost';
        return source.href;
      }

      const normalizedHost = String(host || '').trim();
      const normalizedVersion = String(version || '').trim();
      if (!/^[A-Za-z0-9.-]+(?::\d{1,5})?$/.test(normalizedHost)) return '';
      if (!/^[A-Za-z0-9._-]+$/.test(normalizedVersion)) return '';
      const hostUrl = new URL(`https://${normalizedHost}`);
      if (hostUrl.hostname !== normalizedHost.split(':')[0] || hostUrl.username || hostUrl.password || hostUrl.pathname !== '/') return '';
      const match = source.pathname.match(/\/content\/[^/]+\/(.+)$/);
      if (!match) return '';
      return `https://${normalizedHost}/viewer#${encodeURIComponent(normalizedVersion)}/${match[1]}`;
    } catch {
      return '';
    }
  }

  if (typeof window !== 'undefined') window.buildAuthorUrl = buildAuthorUrl;
  if (typeof module !== 'undefined' && module.exports) module.exports = { buildAuthorUrl };
})();
