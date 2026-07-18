import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'ru.neonco.soberislovo',
  appName: 'Собери слово',
  webDir: 'prototype',
  server: {
    // Грузим уже опубликованный сайт (всегда свежая версия, не надо пересобирать APK при правках контента)
    url: 'https://neonco.github.io/soberi-slovo/',
    cleartext: false,
  },
  android: {
    backgroundColor: '#f4ede1',
  },
};

export default config;
