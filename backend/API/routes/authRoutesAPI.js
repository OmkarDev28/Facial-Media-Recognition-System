import express from 'express';
import pool from '../config/db.js';
import bcrypt from 'bcrypt';
//import session from "express-session";


const router = express.Router();

router.post('/register', async (req, res) => {
    const { username, password, email } = req.body;
    try {
        const existingUser = await pool.query(
            'SELECT * FROM users WHERE username = $1',
            [username]
        );
        if (existingUser.rows.length > 0) {
            return res.status(409).json({ error: 'Username already taken.' });
        }
        const hashedPassword = await bcrypt.hash(password, 10);
        const newUser = await pool.query(
            'INSERT INTO users (username, password, email) VALUES ($1, $2, $3) RETURNING *',
            [username, hashedPassword, email]
        );
        const user = newUser.rows[0];
        req.session.userId = user.id;
        res.status(201).json({
            message: 'User registered and logged in successfully',
            user: { id: user.id, username: user.username }
        });
    } catch (err) {
        console.error('Register error:', err);
        res.status(500).json({ error: 'Server error' });
    }
});

router.post('/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const result = await pool.query(
            'SELECT * FROM users WHERE username=$1',
            [username]
        );
        if (result.rows.length === 0) {
            return res.status(401).json({ error: 'Invalid Credentials' });
        }
        const user = result.rows[0];
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(401).json({ error: 'Invalid Credentials' });
        }
        req.session.userId = user.id;
        
        
        
        res.json({
            message: 'Login Successful',
            user: { id: user.id, username: user.username }
        });
    } catch (err) {
        console.error('Login error:', err);
        res.status(500).json({ error: 'Server error' });
    }
});

router.post('/logout', (req, res) => {
    req.session.destroy(err => {
        if (err) {
            return res.status(500).json({ error: 'Could not log out, please try again.' });
        }
        res.clearCookie('connect.sid');
        res.status(200).json({ message: 'Logout successful' });
    });
});

export default router;
