const translations = {
  en: { title: "FloodIntel", dashboard: "Dashboard", alert: "Alert" },
  te: { title: "FloodIntel", dashboard: "డ్యాష్‌బోర్డ్", alert: "హెచ్చరిక" },
};

export const getTranslation = (lang: string, key: keyof typeof translations['en']) => {
  return translations[lang as keyof typeof translations]?.[key] || translations.en[key];
};
