'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Play, Pause, Volume2, VolumeX, Download, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import Image from 'next/image';

interface ExampleVideo {
  name: string;
  url: string;
  size: number;
  last_modified: string | null;
}

interface VideoPlayerProps {
  video: ExampleVideo;
}

function VideoPlayer({ video }: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [videoRef, setVideoRef] = useState<HTMLVideoElement | null>(null);

  const togglePlay = () => {
    if (videoRef) {
      if (isPlaying) {
        videoRef.pause();
      } else {
        videoRef.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef) {
      videoRef.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = video.url;
    link.download = video.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="group bg-white/10 backdrop-blur-sm rounded-lg overflow-hidden border border-white/20 hover:border-white/40 transition-all duration-300">
      <div className="relative aspect-[9/16] bg-black">
        <video
          ref={setVideoRef}
          src={video.url}
          className="w-full h-full object-contain"
          loop
          muted={isMuted}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onLoadedData={() => {
            // Auto-play on hover might be nice, but let's keep it manual for now
          }}
        />
        
        {/* Video Controls Overlay */}
        <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              size="icon"
              onClick={togglePlay}
              className="h-12 w-12 rounded-full bg-white/20 backdrop-blur-sm hover:bg-white/30"
            >
              {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6" />}
            </Button>
            
            <Button
              variant="secondary"
              size="icon"
              onClick={toggleMute}
              className="h-10 w-10 rounded-full bg-white/20 backdrop-blur-sm hover:bg-white/30"
            >
              {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </Button>
            
            <Button
              variant="secondary"
              size="icon"
              onClick={handleDownload}
              className="h-10 w-10 rounded-full bg-white/20 backdrop-blur-sm hover:bg-white/30"
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
      
      {/* Video Info */}
      <div className="p-4">
        <h3 className="font-medium text-white/90 truncate mb-2">
          {video.name.split('/').pop()?.replace('.mp4', '') || 'Untitled'}
        </h3>
        <div className="text-xs text-white/60 space-y-1">
          <div>Size: {formatFileSize(video.size)}</div>
          <div>Created: {formatDate(video.last_modified)}</div>
        </div>
      </div>
    </div>
  );
}

export default function ExamplesPage() {
  const router = useRouter();
  const [videos, setVideos] = useState<ExampleVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExamples = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`https://veedxfal-backend.gentlefield-cad6f183.uksouth.azurecontainerapps.io/examples`);
      const data = await response.json();
      
      if (data.success) {
        setVideos(data.videos);
      } else {
        setError(data.error || 'Failed to fetch examples');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error fetching examples:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExamples();
  }, []);

  return (
    <main className="min-h-screen relative">
      {/* Background */}
      <div className="fixed inset-0 z-0">
        <Image
          src="/432046b8-76ca-4dfe-a679-c12ef91723b8.png"
          alt="Background"
          fill
          className="object-cover opacity-10"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/30 via-secondary/30 to-accent/30 mix-blend-multiply"></div>
      </div>
      
      {/* Content */}
      <div className="relative z-10 min-h-screen py-12 px-6 sm:px-10 md:px-12 lg:px-24">
        {/* Header */}
        <div className="max-w-7xl mx-auto mb-12">
          <div className="flex items-center gap-4 mb-8">
            <Button
              variant="ghost"
              onClick={() => router.push('/')}
              className="gap-2 text-white/80 hover:text-white hover:bg-white/10"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Button>
          </div>
          
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
              Video <span className="text-secondary">Examples</span>
            </h1>
            <p className="text-lg md:text-xl text-white/80 max-w-2xl mx-auto mb-8">
              Explore our collection of AI-generated videos created from daily journal entries. 
              See the magic of transforming thoughts into visual stories.
            </p>
            
            <div className="flex justify-center gap-4">
              <Button
                variant="outline"
                onClick={fetchExamples}
                className="gap-2 border-white/20 bg-white/5 hover:bg-white/10 text-white"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="max-w-7xl mx-auto text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary mx-auto mb-4"></div>
            <p className="text-white/80">Loading examples...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-2xl mx-auto text-center py-20">
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
              <h3 className="text-red-400 font-medium mb-2">Error Loading Examples</h3>
              <p className="text-red-300/80 mb-4">{error}</p>
              <Button
                variant="outline"
                onClick={fetchExamples}
                className="gap-2 border-red-400/20 bg-red-500/5 hover:bg-red-500/10 text-red-400"
              >
                <RefreshCw className="h-4 w-4" />
                Try Again
              </Button>
            </div>
          </div>
        )}

        {/* Videos Grid */}
        {!loading && !error && (
          <div className="max-w-7xl mx-auto">
            {videos.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-white/60 text-lg mb-4">No example videos found.</p>
                <p className="text-white/40">Check back later for new examples!</p>
              </div>
            ) : (
              <>
                <div className="mb-8 text-center">
                  <p className="text-white/60">
                    Found {videos.length} example video{videos.length !== 1 ? 's' : ''}
                  </p>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {videos.map((video, index) => (
                    <VideoPlayer key={`${video.name}-${index}`} video={video} />
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </main>
  );
} 