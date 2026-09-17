import Cookies from "js-cookie";
import api from "./api";
import { TokenResponse, User } from "@/types";

export async function loginUser(email: string, password: string): Promise<User> {
  // FastAPI's OAuth2PasswordRequestForm expects `application/x-www-form-urlencoded`
  // with `username` (= email) and `password` fields.
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const { data } = await api.post<TokenResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  persistSession(data);
  return data.user;
}

export async function registerUser(
  full_name: string,
  email: string,
  password: string
): Promise<User> {
  const { data } = await api.post<TokenResponse>("/auth/register", {
    full_name,
    email,
    password,
  });
  persistSession(data);
  return data.user;
}

function persistSession(data: TokenResponse) {
  Cookies.set("access_token", data.access_token, { expires: 1 });
  Cookies.set("refresh_token", data.refresh_token, { expires: 7 });
  Cookies.set("user", JSON.stringify(data.user), { expires: 7 });
}

export function logoutUser() {
  Cookies.remove("access_token");
  Cookies.remove("refresh_token");
  Cookies.remove("user");
  if (typeof window !== "undefined") window.location.href = "/login";
}

export function getStoredUser(): User | null {
  const raw = Cookies.get("user");
  return raw ? (JSON.parse(raw) as User) : null;
}

export function isAuthenticated(): boolean {
  return !!Cookies.get("access_token");
}
