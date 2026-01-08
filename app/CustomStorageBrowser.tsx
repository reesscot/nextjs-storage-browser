'use client';
import React, { useEffect } from 'react';
import {
  createStorageBrowser,
  createAmplifyAuthAdapter,
  elementsDefault,
} from '@aws-amplify/ui-react-storage/browser';

export default function CustomStorageBrowser() {
  const { StorageBrowser } = createStorageBrowser({
    elements: elementsDefault,
    config: createAmplifyAuthAdapter({
      options: {
        defaultPrefixes: [
          'ConversionFiles/',
          'ConversionFileErrors/',
          'InitialUpload/',
          'InitialUploadErrors/',
          'TSQLFiles/',
          'DataValidation/',
        ],
      },
    }),
  });

  useEffect(() => {
    // Check if there's a target path in sessionStorage
    const targetPath = sessionStorage.getItem('s3NavigationTarget');
    if (targetPath) {
      // Find the StorageBrowser component and navigate to the target path
      const storageBrowserElement = document.querySelector('[data-amplify-storage-browser]');
      if (storageBrowserElement) {
        // Clear the target path from sessionStorage
        sessionStorage.removeItem('s3NavigationTarget');
        
        // Use the StorageBrowser's internal navigation
        // This is a simplified approach - actual implementation may vary based on the StorageBrowser's API
        const pathParts = targetPath.split('/').filter(Boolean);
        
        // Allow time for the StorageBrowser to initialize
        setTimeout(() => {
          // Find and click on folder items that match the path parts
          pathParts.forEach(part => {
            const folderItems = document.querySelectorAll('[data-amplify-storage-item]');
            folderItems.forEach(item => {
              if (item.textContent?.includes(part)) {
                (item as HTMLElement).click();
              }
            });
          });
        }, 500);
      }
    }
  }, []);

  return <StorageBrowser />;
}