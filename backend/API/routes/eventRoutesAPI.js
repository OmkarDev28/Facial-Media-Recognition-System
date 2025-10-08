import express from 'express';
import pool from '../config/db.js';

const router = express.Router();

// Middleware to ensure a user is logged in
const requireLogin = (req, res, next) => {
    if (!req.session.userId) {
        return res.status(401).json({ error: 'You must be logged in.' });
    }
    next();
};

router.post('/create-event', requireLogin, async (req, res) => {
    const { title, description } = req.body;
    
    const creatorId = req.session.userId; 


    if (!title) {
        return res.status(400).json({ error: 'Title is required' });
    }

    try {
        const newEvent = await pool.query(
            'INSERT INTO events (creator_id, title, description) VALUES ($1, $2, $3) RETURNING *',
            [creatorId, title, description]
        );

        res.status(201).json({
            message: 'Event created successfully',
            event: newEvent.rows[0],
        });
    } catch (err) {
        console.error('Create event error:', err);
        res.status(500).json({ error: 'Server error' });
    }
});

router.delete('/delete-event/:eventId', requireLogin, (req, res) => {
    const {eventId} = req.params;
    const creatorId = req.session.userId;

    try{
      const deletedEvent = pool.query(
        'DELETE FROM events WHERE id=$1 RETURNING title', [eventId]
      );

      res.status(201).json({ 
        message: "Event deleated successfully.",
        deletedEvent: deletedEvent.rows[0]
      });
    }
    catch (err) {
        console.error('Error while deleting event:', err);
        res.status(500).json({ error: 'Server error' });
    }
});



export default router;