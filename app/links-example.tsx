'use client';
import React from 'react';
import S3FolderLink from './S3FolderLink';

export default function LinksExample() {
  return (
    <div>
      <h1>S3 Folder Links</h1>
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
  );
}