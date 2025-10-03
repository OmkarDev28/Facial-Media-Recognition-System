import express from 'express';
import pool from '../config/db.js';
import passport from 'passport';

const router = express.Router();


router.post('/events'  , async (req, res) => {
    const { title, description } = req.body;
    const creatorId = 5; 

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
  }
);



export default router;
