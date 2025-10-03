import express from 'express';
import pool from '../config/db.js';
import passport from 'passport';

const router = express.Router();

// ----------------------
// Protected Upload Route
// ----------------------
router.post("/media/upload", passport.authenticate("jwt", { session: false }), // ✅ Protect this route
  async (req, res) => {
    try {
      const userId = req.user.id; 
      const { fileUrl, description, file_type } = req.body; // example data

      // insert into DB
      const result = await pool.query(
        "INSERT INTO media (user_id, file_url, file_type, description) VALUES ($1, $2, $3, $4) RETURNING *",
        [userId, fileUrl, file_type, description]
      );

      res.status(201).json({
        message: "Media uploaded successfully",
        media: result.rows[0],
      });
    } catch (err) {
      console.error("Upload error:", err);
      res.status(500).json({ error: "Server error" });
    }
  }
);

router.post("/media/list", passport.authenticate("jwt", { session: false }), // ✅ Protect this route
  async (req, res) => {
    
    try{
      const userId = req.user.id;

      const result = await pool.query(
        "SELECT * FROM media WHERE user_id = $1",
        [userId]
      );

      res.status(201).json({
        message: "Media listed",
        media: result,
      });
    } catch (err) {
      console.error("Upload error:", err);
      res.status(500).json({ error: "Server error" });
    }
  })

export default router;
