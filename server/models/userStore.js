// Simple file-based user store for local development
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcrypt');

const USERS_FILE = path.join(__dirname, 'users.json');

function readUsers() {
  if (!fs.existsSync(USERS_FILE)) return [];
  return JSON.parse(fs.readFileSync(USERS_FILE, 'utf8'));
}

function writeUsers(users) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
}

function findUserByUsername(username) {
  const users = readUsers();
  return users.find(u => u.username === username);
}

function addUser({ username, password, services, avatar }) {
  const users = readUsers();
  if (users.find(u => u.username === username)) return false;
  const hash = bcrypt.hashSync(password, 10);
  users.push({ username, password: hash, services, avatar });
  writeUsers(users);
  return true;
}

function validateUser(username, password) {
  const user = findUserByUsername(username);
  if (!user) return false;
  return bcrypt.compareSync(password, user.password) ? user : false;
}

module.exports = {
  readUsers,
  writeUsers,
  findUserByUsername,
  addUser,
  validateUser,
};
