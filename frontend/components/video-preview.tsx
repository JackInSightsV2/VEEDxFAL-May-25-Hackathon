"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Share2, Download, RefreshCw, Facebook, Instagram, Twitter } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface VideoPreviewProps {
  videoUrl: string;
  onCreateNew: () => void;
}

// Custom TikTok icon as it's not in Lucide
function TiktokIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5"></path>
    </svg>
  );
}

export default function VideoPreview({ videoUrl, onCreateNew }: VideoPreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = videoUrl;
    link.download = 'my-journal-video.mp4';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  const handleShareTo = (platform: string) => {
    // In a real app, this would integrate with platform-specific APIs
    // For now, we'll just show what would happen
    alert(`Sharing to ${platform}. In a production app, this would open the ${platform} sharing flow.`);
  };

  return (
    <div className="p-6 md:p-8">
      <h2 className="text-2xl font-bold mb-6 text-center">Your Video is Ready!</h2>
      
      <div className="relative rounded-lg overflow-hidden bg-black mb-6 aspect-[9/16] max-w-[400px] mx-auto">
        <video
          src={videoUrl}
          className="w-full h-full object-contain"
          controls
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />
      </div>
      
      <div className="flex flex-col sm:flex-row justify-center gap-4 mb-8">
        <Button variant="outline" onClick={handleDownload} className="gap-2">
          <Download className="h-4 w-4" />
          Download
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button className="gap-2">
              <Share2 className="h-4 w-4" />
              Share to Social
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="center">
            <DropdownMenuItem onClick={() => handleShareTo('TikTok')} className="gap-2 cursor-pointer">
              <TiktokIcon className="h-4 w-4" />
              <span>TikTok</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleShareTo('Instagram')} className="gap-2 cursor-pointer">
              <Instagram className="h-4 w-4" />
              <span>Instagram</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleShareTo('Twitter')} className="gap-2 cursor-pointer">
              <Twitter className="h-4 w-4" />
              <span>Twitter</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleShareTo('Facebook')} className="gap-2 cursor-pointer">
              <Facebook className="h-4 w-4" />
              <span>Facebook</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      
      <div className="text-center">
        <Button variant="ghost" onClick={onCreateNew} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Create a New Video
        </Button>
      </div>
    </div>
  );
}