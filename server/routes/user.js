// User routes (protected)
const express = require('express');
const router = express.Router();

// Middleware to check authentication
function ensureAuthenticated(req, res, next) {
  if (req.isAuthenticated()) return next();
  res.status(401).json({ error: 'Non autorizzato' });
}

// Example protected route
router.get('/profile', ensureAuthenticated, (req, res) => {
  res.json({ user: req.user });
});

module.exports = router;
