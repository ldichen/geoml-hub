import { g as get_store_value } from "./utils.js";
import { u as user } from "./auth.js";
function getCurrentUser() {
  return get_store_value(user);
}
function isOwner(resourceOwner) {
  const currentUser = getCurrentUser();
  return currentUser && (currentUser.username === resourceOwner || currentUser.id === resourceOwner || currentUser.is_admin);
}
export {
  isOwner as i
};
