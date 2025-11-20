import { w as writable } from "./index.js";
const user = writable(null);
const isAuthenticated = writable(false);
const authToken = writable(null);
function logout() {
  authToken.set(null);
  user.set(null);
  isAuthenticated.set(false);
}
export {
  authToken,
  isAuthenticated,
  logout,
  user
};
