"use client";

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, Video, File, X, ArrowRight } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface VideoUploadProps {
  onSubmit: (file: File) => void;
}

export default function VideoUpload({ onSubmit }: VideoUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Validate file type
    if (!file.type.startsWith('video/')) {
      alert('Please upload a video file');
      return;
    }
    
    setFile(file);
    
    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += 5;
      setUploadProgress(progress);
      if (progress >= 100) {
        clearInterval(interval);
      }
    }, 100);
  };

  const removeFile = () => {
    setFile(null);
    setUploadProgress(0);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleSubmit = () => {
    if (file) {
      onSubmit(file);
    }
  };

  return (
    <div className="space-y-6">
      {!file ? (
        <div
          className={cn(
            "border-2 border-dashed rounded-lg p-12 text-center transition-all",
            dragActive 
              ? "border-primary bg-primary/5" 
              : "border-border hover:border-primary/50 hover:bg-muted/50"
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            type="file"
            id="file-upload"
            onChange={handleChange}
            accept="video/*"
            className="hidden"
          />
          
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="rounded-full bg-muted p-3">
              <Upload className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <p className="text-base font-medium">
                Drag and drop your video here
              </p>
              <p className="text-sm text-muted-foreground">
                Support for MP4, MOV, and WEBM files
              </p>
            </div>
            <Button 
              variant="outline" 
              onClick={() => inputRef.current?.click()}
              type="button"
            >
              Select Video
            </Button>
          </div>
        </div>
      ) : (
        <div className="border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="rounded-full bg-primary/10 p-2">
                <Video className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium truncate max-w-[180px] sm:max-w-[300px]">
                  {file.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={removeFile}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="h-2" />
          </div>
        </div>
      )}
      
      <Button 
        onClick={handleSubmit}
        disabled={!file || uploadProgress < 100}
        className="w-full gap-2"
      >
        Continue
        <ArrowRight size={16} />
      </Button>
    </div>
  );
}