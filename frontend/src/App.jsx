import { useState } from "react";
import Login from "./pages/Login.jsx";
import Home from "./pages/Home.jsx";

export default function App() {
  const [auth, setAuth] = useState(() => {
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");
    return token && username ? { token, username } : null;
  });

  function handleLogin({ access_token, username }) {
    localStorage.setItem("token", access_token);
    localStorage.setItem("username", username);
    setAuth({ token: access_token, username });
  }

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setAuth(null);
  }

  if (!auth) {
    return <Login onLogin={handleLogin} />;
  }
  return <Home auth={auth} onLogout={handleLogout} />;
}
