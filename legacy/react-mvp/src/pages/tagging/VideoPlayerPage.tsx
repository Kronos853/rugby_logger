import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { createBroadcastChannel, postMessage, subscribe } from '../../lib/broadcast';
import '../../tagging.css';

export function VideoPlayerPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const videoRef = useRef<HTMLVideoElement>(null);
  const channelRef = useRef(createBroadcastChannel());
  const [ready, setReady] = useState(false);

  useEffect(() => {
    document.body.classList.add('video-page');
    return () => document.body.classList.remove('video-page');
  }, []);

  useEffect(() => {
    const channel = channelRef.current;
    const video = videoRef.current;

    const unsubscribe = subscribe(channel, (msg) => {
      if (!video) return;
      if (msg.type === 'PAUSE') video.pause();
      if (msg.type === 'TOGGLE_PLAY') {
        if (video.paused) void video.play();
        else video.pause();
      }
      if (msg.type === 'SEEK') {
        video.currentTime = msg.time;
        video.pause();
      }
      if (msg.type === 'CONNECTED') {
        postMessage(channel, { type: 'TIME_UPDATE', time: video.currentTime });
      }
    });

    postMessage(channel, { type: 'CONNECTED' });
    return unsubscribe;
  }, [ready]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onTimeUpdate = () => {
      postMessage(channelRef.current, { type: 'TIME_UPDATE', time: video.currentTime });
    };

    video.addEventListener('timeupdate', onTimeUpdate);
    return () => video.removeEventListener('timeupdate', onTimeUpdate);
  }, [ready]);

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    const video = videoRef.current;
    if (!file || !video) return;
    video.src = URL.createObjectURL(file);
    setReady(true);
    void video.play();
  }

  return (
    <div className="video-page">
      {!ready && (
        <div className="video-setup">
          <h2>Матч #{matchId} — выберите видеофайл</h2>
          <input type="file" accept="video/*" onChange={handleFile} />
        </div>
      )}
      <video ref={videoRef} className="video-player" controls style={{ display: ready ? 'block' : 'none' }} />
    </div>
  );
}
