'use client';
import { useRouter } from 'next/navigation';
import React from 'react';

interface S3FolderLinkProps {
  path: string;
  children: React.ReactNode;
}

export default function S3FolderLink({ path, children }: S3FolderLinkProps) {
  const router = useRouter();
  
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    
    // Store the target path in sessionStorage
    sessionStorage.setItem('s3NavigationTarget', path);
    
    // Refresh the page to trigger the navigation in StorageBrowser
    router.refresh();
  };

  return (
    <a href="#" onClick={handleClick}>
      {children}
    </a>
  );
}