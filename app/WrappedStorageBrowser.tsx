import React from 'react';
import { uploadData } from 'aws-amplify/storage';
import StorageBrowser from './StorageBrowser';

interface WrappedStorageBrowserProps {
  [key: string]: any; // Allow passing all props
}

const WrappedStorageBrowser: React.FC<WrappedStorageBrowserProps> = (props) => {
  /**
   * Custom uploadData function that adds an S3 tag.
   */
  const uploadDataWithTags = async ({ path, data, options }: any) => {
    try {
      const result = await uploadData({
        path,
        data,
        options: {
          metadata: {
            'customKey': 'TestCustomKey', // Replace with actual tag key-value pair
          },
        },
      });

      console.log('File uploaded successfully with tagging:', result);
      return result;
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  };

  return (
    <div>
      {/* Pass all other props to StorageBrowser */}
      <StorageBrowser {...props} />
      
      {/* Custom upload button to call uploadDataWithTags */}
      <input
        type="file"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            uploadDataWithTags({ path: `uploads/${file.name}`, data: file });
          }
        }}
      />
    </div>
  );
};

export default WrappedStorageBrowser;
