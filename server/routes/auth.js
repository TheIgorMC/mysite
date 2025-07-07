// Auth routes (register, login, logout, email verification, 2FA placeholder)
const express = require('express');
const passport = require('passport');
const User = require('../models/User');
const router = express.Router();

// Register
router.post('/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    const user = new User({ username, email, password });
    await user.save();
    // TODO: Send verification email
    res.status(201).json({ message: 'Registrazione avvenuta. Controlla la tua email.' });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Login
router.post('/login', (req, res, next) => {
  passport.authenticate('local', (err, user, info) => {
    if (err) return next(err);
    if (!user) return res.status(401).json({ error: info.message });
    req.logIn(user, err => {
      if (err) return next(err);
      res.json({ message: 'Login effettuato', user: { username: user.username, email: user.email } });
    });
  })(req, res, next);
});

// Logout
router.post('/logout', (req, res) => {
  req.logout(() => {
    res.json({ message: 'Logout effettuato' });
  });
});

// Placeholder for email verification and 2FA
// ...

module.exports = router;
