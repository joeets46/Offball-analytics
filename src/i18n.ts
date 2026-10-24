import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en/common.json'
import tr from './locales/tr/common.json'

const storageKey = 'offball-language'
const storedLanguage = localStorage.getItem(storageKey)
const browserLanguage = navigator.language.toLowerCase().startsWith('tr') ? 'tr' : 'en'

void i18n
  .use(initReactI18next)
  .init({
    resources: { en: { common: en }, tr: { common: tr } },
    lng: storedLanguage === 'tr' || storedLanguage === 'en' ? storedLanguage : browserLanguage,
    fallbackLng: 'en',
    defaultNS: 'common',
    interpolation: { escapeValue: false },
  })

i18n.on('languageChanged', (language) => {
  localStorage.setItem(storageKey, language)
})

export default i18n
