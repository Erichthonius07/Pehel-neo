"use client";

import { useState, useEffect } from 'react';

const CITIZEN_TOKEN_KEY = 'pehel_citizen_token';
const AUTHORITY_TOKEN_KEY = 'pehel_authority_token';

export function useAuth() {
  const [citizenToken, setCitizenToken] = useState<string | null>(null);
  const [authorityToken, setAuthorityToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const c = localStorage.getItem(CITIZEN_TOKEN_KEY);
    const a = localStorage.getItem(AUTHORITY_TOKEN_KEY);
    if (c) setCitizenToken(c);
    if (a) setAuthorityToken(a);
    setIsLoading(false);
  }, []);

  return {
    citizenToken,
    authorityToken,
    isLoading,
    isCitizen: !!citizenToken,
    isAuthority: !!authorityToken,
    loginCitizen: (token: string) => { localStorage.setItem(CITIZEN_TOKEN_KEY, token); setCitizenToken(token); },
    loginAuthority: (token: string) => { localStorage.setItem(AUTHORITY_TOKEN_KEY, token); setAuthorityToken(token); },
    logout: () => { localStorage.removeItem(CITIZEN_TOKEN_KEY); localStorage.removeItem(AUTHORITY_TOKEN_KEY); setCitizenToken(null); setAuthorityToken(null); },
  };
}

export function getCitizenToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(CITIZEN_TOKEN_KEY);
}

export function getAuthorityToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTHORITY_TOKEN_KEY);
}