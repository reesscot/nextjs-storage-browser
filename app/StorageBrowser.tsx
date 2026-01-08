import { StorageBrowser } from '@aws-amplify/ui-react-storage';

// these should match access patterns defined in amplify/storage/resource.ts
const defaultPrefixes = [
  'ConversionFiles/',
  'ConversionFileErrors/',
  'InitialUpload/',
  'InitialUploadErrors/',
  'TSQLFiles/',
  'DataValidation/',
  //(identityId: string) => `protected/${identityId}/`,
  //(identityId: string) => `private/${identityId}/`,
];

export default function Example() {
  return (
    <StorageBrowser defaultPrefixes={defaultPrefixes} />
  )
}