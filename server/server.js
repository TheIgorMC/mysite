// Entry point for the backend server
const express = require('express');
const session = require('express-session');
const passport = require('passport');
const path = require('path');
const dotenv = require('dotenv');
const userStore = require('./models/userStore');
const LocalStrategy = require('passport-local').Strategy;

// Load environment variables
dotenv.config({ path: path.join(__dirname, 'config', '.env') });

const app = express();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Session config (in-memory, for local dev)
app.use(session({
  secret: process.env.SESSION_SECRET || 'dev-secret',
  resave: false,
  saveUninitialized: false,
  // No store: in-memory only
}));

// Passport config
passport.use(new LocalStrategy((username, password, done) => {
  const user = userStore.validateUser(username, password);
  if (!user) return done(null, false, { message: 'Invalid credentials' });
  return done(null, user);
}));
passport.serializeUser((user, done) => {
  done(null, user.username);
});
passport.deserializeUser((username, done) => {
  const user = userStore.findUserByUsername(username);
  done(null, user || false);
});
app.use(passport.initialize());
app.use(passport.session());

// Auth endpoints
app.post('/api/register', (req, res) => {
  const { username, password, services, avatar } = req.body;
  if (!username || !password || !services) return res.status(400).json({ error: 'Missing fields' });
  const ok = userStore.addUser({ username, password, services, avatar });
  if (!ok) return res.status(409).json({ error: 'User exists' });
  res.json({ success: true });
});

app.post('/api/login', passport.authenticate('local'), (req, res) => {
  res.json({ success: true, user: { username: req.user.username, services: req.user.services, avatar: req.user.avatar } });
});

app.post('/api/logout', (req, res) => {
  req.logout(() => {
    res.json({ success: true });
  });
});

app.get('/api/session', (req, res) => {
  if (req.isAuthenticated()) {
    const { username, services, avatar } = req.user;
    res.json({ authenticated: true, user: { username, services, avatar } });
  } else {
    res.json({ authenticated: false });
  }
});

// Middleware to protect routes
function ensureAuthenticated(req, res, next) {
  if (req.isAuthenticated()) return next();
  res.status(401).json({ error: 'Not authenticated' });
}

// Example protected route
app.get('/api/protected', ensureAuthenticated, (req, res) => {
  res.json({ message: 'You are authenticated', user: req.user });
});

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/user', require('./routes/user'));

// Serve static frontend
app.use(express.static(path.join(__dirname, '..')));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
