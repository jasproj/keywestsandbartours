// ===== VIDEO OPTIMIZATION FOR MOBILE =====
// Disable autoplay on mobile/3G, lazy load videos

document.addEventListener('DOMContentLoaded', () => {
    const videos = document.querySelectorAll('video[autoplay]');
    
    // Check if on mobile or slow connection
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const mediaQuery = window.matchMedia('(max-width: 768px)');
    
    // Check connection speed
    if (navigator.connection) {
        const effectiveType = navigator.connection.effectiveType;
        const isSlowConnection = effectiveType === '3g' || effectiveType === '4g';
        
        videos.forEach(video => {
            // Disable autoplay on mobile
            if (isMobile || mediaQuery.matches) {
                video.autoplay = false;
                video.poster = video.getAttribute('data-poster') || '';
                
                // Add play button hint
                const playBtn = document.createElement('div');
                playBtn.style.cssText = `
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 60px;
                    height: 60px;
                    background: rgba(255,255,255,0.8);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    z-index: 10;
                    font-size: 30px;
                `;
                playBtn.innerHTML = '▶';
                playBtn.addEventListener('click', () => {
                    video.play();
                    playBtn.style.display = 'none';
                });
                
                if (video.parentElement) {
                    video.parentElement.style.position = 'relative';
                    video.parentElement.appendChild(playBtn);
                }
            }
            
            // Lazy load video if slow connection
            if (isSlowConnection) {
                video.preload = 'none';
                const sources = video.querySelectorAll('source');
                sources.forEach(source => {
                    source.setAttribute('data-src', source.getAttribute('src'));
                    source.removeAttribute('src');
                });
                
                // Load when video is visible
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const sources = entry.target.querySelectorAll('source');
                            sources.forEach(source => {
                                source.setAttribute('src', source.getAttribute('data-src'));
                            });
                            entry.target.load();
                            observer.unobserve(entry.target);
                        }
                    });
                });
                observer.observe(video);
            }
        });
    }
});
