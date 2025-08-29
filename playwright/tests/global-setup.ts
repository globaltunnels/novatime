import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  // This function can be used to set up test data, authenticate users, etc.
  // For now, we'll keep it simple
  console.log('Global setup completed');
}

export default globalSetup;