'use client';
import React, { useEffect, useState } from 'react';
import { Amplify } from 'aws-amplify';
import { signOut, fetchUserAttributes } from 'aws-amplify/auth';
import { Button, withAuthenticator } from '@aws-amplify/ui-react';
import {
  createStorageBrowser,
  createAmplifyAuthAdapter,
  elementsDefault,
} from '@aws-amplify/ui-react-storage/browser';
import '@aws-amplify/ui-react-storage/styles.css';
import '@aws-amplify/ui-react-storage/storage-browser-styles.css';
import S3FolderLink from './S3FolderLink';
import config from '../amplify_outputs.json';

Amplify.configure(config);

function Example() {
  const [currentPath, setCurrentPath] = useState('');
  
  useEffect(() => {
    // Check if there's a target path in sessionStorage
    const targetPath = sessionStorage.getItem('s3NavigationTarget');
    if (targetPath) {
      setCurrentPath(targetPath);
      // Clear the target path from sessionStorage after using it
      sessionStorage.removeItem('s3NavigationTarget');
    }
    
    async function getAttributes() {
      try {
        const attributes = await fetchUserAttributes();
        console.log("User Attributes:", attributes);
      } catch (error) {
        console.error("Error fetching user attributes", error);
      }
    }
    getAttributes();
  }, []);

  const { StorageBrowser } = createStorageBrowser({
    elements: elementsDefault,
    config: createAmplifyAuthAdapter({
      options: {
        defaultPrefixes: [
          'ConversionFiles/',
          'ConversionFileErrors/',
          'ConversionFileErrors/Mock8/',
          'InitialUpload/',
          'InitialUploadErrors/',
          'TSQLFiles/',
          'DataValidation/',
        ],
        // Set the initial path if one is specified
        ...(currentPath && { initialPath: currentPath }),
      },
    }),
  });

  return (
    <>
      <Button
        marginBlockEnd="xl"
        size="small"
        onClick={() => {
          signOut();
        }}
      >
        Sign Out
      </Button>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Quick Links:</h3>
        <ul>
          <li>
            <S3FolderLink path="ConversionFileErrors/Mock8">
              Go to ConversionFileErrors/Mock8
            </S3FolderLink>
          </li>
          <li>
            <S3FolderLink path="haciendaerp/conversionfileerrors">
              Go to haciendaerp/conversionfileerrors
            </S3FolderLink>
          </li>
        </ul>
      </div>
      
      <StorageBrowser />
    </>
  );
}

export default withAuthenticator(Example);