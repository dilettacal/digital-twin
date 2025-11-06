'use client';

import { useState } from 'react';
import Image from 'next/image';

interface AvatarProps {
  src: string;
  alt: string;
  size: number;
  showBadge?: boolean;
  badgeColor?: string;
  fallbackText?: string;
  className?: string;
}

export function Avatar({ 
  src, 
  alt, 
  size, 
  showBadge = false, 
  badgeColor = 'green',
  fallbackText,
  className = ''
}: AvatarProps) {
  const [imageError, setImageError] = useState(false);

  const getInitials = () => {
    if (fallbackText) return fallbackText;
    // Extract initials from alt text
    const words = alt.split(' ');
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase();
    }
    return alt.substring(0, 2).toUpperCase();
  };

  return (
    <div className={`relative ${className}`}>
      <div 
        className={`rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 ring-2 ring-white shadow-md overflow-hidden`}
        style={{ width: size, height: size }}
      >
        {!imageError ? (
          <Image
            src={src}
            alt={alt}
            width={size}
            height={size}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-bold" style={{ fontSize: size * 0.35 }}>
            {getInitials()}
          </div>
        )}
      </div>
      {showBadge && (
        <div 
          className={`absolute bottom-0 right-0 rounded-full border-2 border-white`}
          style={{ 
            width: size >= 40 ? '14px' : '12px', 
            height: size >= 40 ? '14px' : '12px',
            backgroundColor: badgeColor === 'green' ? '#10b981' : '#6366f1'
          }}
        ></div>
      )}
    </div>
  );
}

interface LargeAvatarProps {
  src: string;
  alt: string;
  showBadge?: boolean;
  fallbackText?: string;
}

export function LargeAvatar({ src, alt, showBadge = true, fallbackText = 'DT' }: LargeAvatarProps) {
  const [imageError, setImageError] = useState(false);

  return (
    <div className="relative">
      <div className="w-32 h-32 rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-1 shadow-xl">
        <div className="w-full h-full rounded-full bg-white p-1">
          {!imageError ? (
            <Image
              src={src}
              alt={alt}
              width={120}
              height={120}
              className="w-full h-full rounded-full object-cover"
              priority
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-3xl font-bold">
              {fallbackText}
            </div>
          )}
        </div>
      </div>
      {showBadge && (
        <div className="absolute bottom-0 right-0 w-8 h-8 bg-green-500 rounded-full border-4 border-white shadow-lg flex items-center justify-center">
          <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
        </div>
      )}
    </div>
  );
}

