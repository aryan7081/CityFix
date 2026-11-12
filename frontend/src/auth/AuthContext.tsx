import React, { createContext, useContext, useMemo, useState } from "react";
import { api } from "../api/client";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  login: (username: string, password: string) => Promise<User>;
  register: (payload: Record<string, string>) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

function loadUser(): User | null {
  const raw = localStorage.getItem("cityfix_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(loadUser);

  const login = async (username: string, password: string) => {
    const { data } = await api.post("/auth/login/", { username, password });
    localStorage.setItem("cityfix_access", data.access);
    localStorage.setItem("cityfix_refresh", data.refresh);
    localStorage.setItem("cityfix_user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user as User;
  };

  const register = async (payload: Record<string, string>) => {
    await api.post("/auth/register/", payload);
  };

  const logout = () => {
    localStorage.removeItem("cityfix_access");
    localStorage.removeItem("cityfix_refresh");
    localStorage.removeItem("cityfix_user");
    setUser(null);
  };

  const value = useMemo(
    () => ({
      user,
      login,
      register,
      logout,
      isAuthenticated: !!user,
    }),
    [user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
