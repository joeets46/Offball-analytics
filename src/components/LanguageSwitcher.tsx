import { useTranslation } from 'react-i18next'

export default function LanguageSwitcher() {
  const { i18n } = useTranslation()
  const language = i18n.language.startsWith('tr') ? 'tr' : 'en'

  return (
    <label className="language-switcher">
      <span className="sr-only">Language</span>
      <select
        aria-label="Language"
        value={language}
        onChange={(event) => void i18n.changeLanguage(event.target.value)}
      >
        <option value="en">EN</option>
        <option value="tr">TR</option>
      </select>
    </label>
  )
}
