import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { fetchMe, login as apiLogin, register as apiRegister } from "../api/auth";
import { setUnauthorizedHandler } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("jwt"));
  const [username, setUsername] = useState(() => localStorage.getItem("username"));
  const [ready, setReady] = useState(false);

  const logout = useCallback(() => {
    localStorage.removeItem("jwt");
    localStorage.removeItem("username");
    setToken(null);
    setUsername(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
  }, [logout]);

  useEffect(() => {
    if (!token) {
      setReady(true);
      return;
    }
    fetchMe()
      .then((me) => setUsername(me.username))
      .catch(() => logout())
      .finally(() => setReady(true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(username, password) {
    const data = await apiLogin(username, password);
    localStorage.setItem("jwt", data.access_token);
    localStorage.setItem("username", username);
    setToken(data.access_token);
    setUsername(username);
  }

  async function register(username, password) {
    await apiRegister(username, password);
    await login(username, password);
  }

  return (
    <AuthContext.Provider value={{ token, username, ready, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
