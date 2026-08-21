import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type ThemePreference = 'light' | 'dark' | 'system';
type ResolvedTheme = 'light' | 'dark';

type ThemeState = {
  theme: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: ThemePreference) => void;
};

type StoredTheme = { version: 1; preference: ThemePreference };

const THEME_STORAGE_KEY = 'risksim.theme.v1';
const ThemeContext = createContext<ThemeState | null>(null);

function systemTheme(): ResolvedTheme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function readTheme(): ThemePreference {
  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (!raw) return 'system';
    const stored = JSON.parse(raw) as StoredTheme;
    return stored.version === 1 && ['light', 'dark', 'system'].includes(stored.preference)
      ? stored.preference
      : 'system';
  } catch {
    window.localStorage.removeItem(THEME_STORAGE_KEY);
    return 'system';
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemePreference>(readTheme);
  const [systemPreference, setSystemPreference] = useState<ResolvedTheme>(systemTheme);
  const resolvedTheme = theme === 'system' ? systemPreference : theme;

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const update = () => setSystemPreference(media.matches ? 'dark' : 'light');
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  const setTheme = useCallback((preference: ThemePreference) => {
    const stored: StoredTheme = { version: 1, preference };
    window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(stored));
    setThemeState(preference);
  }, []);

  const value = useMemo(
    () => ({ theme, resolvedTheme, setTheme }),
    [resolvedTheme, setTheme, theme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error('useTheme doit être utilisé dans ThemeProvider');
  return value;
}
