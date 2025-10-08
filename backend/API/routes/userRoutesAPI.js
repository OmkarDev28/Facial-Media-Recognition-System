import express from 'express';
import pool from '../config/db.js';

const router = express.Router();

const requireLogin = (req, res, next) => {
    if (!req.session.userId) {
        return res.status(401).json({ error: 'You must be logged in.' });
    }
    next();
};

router.post('/register-for-event/:eventId', requireLogin, async(req, res) => {
    const userId = req.session.userId;
    const {eventId} = parseInt(req.params.eventId);

    const eventResult = await pool.query(
            'SELECT event_id FROM event_participation WHERE event_id = $1',
            [eventId]
        );

    if (eventResult.rowCount === 0) {
        
        return res.status(404).json({ message: "Event not found." });
    }

    try{

        const result = await pool.query(
            `SELECT * FROM event_participation 
            WHERE event_id = $1 AND user_id = $2`,
            [eventId, userId]
        );

        if (result.rows.length === 1){
            return res.status(409).json({ message: "User is already registered"});
        }
        else {
            await pool.query(
                'INSERT INTO event_participation (user_id, event_id) VALUES ($1, $2)', [userId, eventId]
            );
            return res.status(201).json({ message: "User registered for event successfully."});
        }
        
    } catch (error) {
        console.error('Register error:', error);
        res.status(500).json({ error: 'Server error' });
    }
});

export default router;
